# -*- coding: utf-8 -*-
"""Windows Jump List files:
* .automaticDestinations-ms
* .customDestinations-ms
"""

import datetime
import logging
import os

import pyfwsi
import pylnk
import pyolecf

from dtfabric import errors as dtfabric_errors
from dtfabric import fabric as dtfabric_fabric

from dtformats import data_format
from dtformats import data_range
from dtformats import errors


def FromFiletime(filetime):
  """Converts a FILETIME timestamp into a Python datetime object.

  The FILETIME is mainly used in Windows file formats and NTFS.

  The FILETIME is a 64-bit value containing:
  100th nano seconds since 1601-01-01 00:00:00

  Technically FILETIME consists of 2 x 32-bit parts and is presumed
  to be unsigned.

  Args:
    filetime (int): 64-bit FILETIME timestamp.

  Returns:
    datetime: date and time or None.
  """
  if filetime < 0:
    return

  timestamp, _ = divmod(filetime, 10)

  return datetime.datetime(1601, 1, 1) + datetime.timedelta(
      microseconds=timestamp)


class LNKFileEntry(object):
  """Windows Shortcut (LNK) file entry.

  Attributes:
    data_size (int): size of the LNK file entry data.
    identifier (str): LNK file entry identifier.
  """

  def __init__(self, identifier):
    """Initializes the LNK file entry object.

    Args:
      identifier (str): LNK file entry identifier.
    """
    super(LNKFileEntry, self).__init__()
    self._lnk_file = pylnk.file()
    self.identifier = identifier
    self.data_size = 0

  def Close(self):
    """Closes the LNK file entry."""
    self._lnk_file.close()

  def GetShellItems(self):
    """Retrieves the shell items.

    Yields:
      pyfswi.item: shell item.
    """
    if self._lnk_file.link_target_identifier_data:
      shell_item_list = pyfwsi.item_list()
      shell_item_list.copy_from_byte_stream(
          self._lnk_file.link_target_identifier_data)

      for shell_item in iter(shell_item_list.items):
        yield shell_item

  def Open(self, file_object):
    """Opens the LNK file entry.

    Args:
      file_object (file): file-like object that contains the LNK file
          entry data.
    """
    self._lnk_file.open_file_object(file_object)

    # We cannot trust the file size in the LNK data so we get the last offset
    # that was read instead. Because of DataRange the offset will be relative
    # to the start of the LNK data.
    self.data_size = file_object.get_offset()


class AutomaticDestinationsFile(data_format.BinaryDataFile):
  """Automatic Destinations Jump List (.automaticDestinations-ms) file.

  Attributes:
    entries (list[LNKFileEntry]): LNK file entries.
    recovered_entries (list[LNKFileEntry]): recovered LNK file entries.
  """

  _DATA_TYPE_FABRIC_DEFINITION = b'\n'.join([
      b'name: char',
      b'type: character',
      b'attributes:',
      b'  size: 1',
      b'  units: bytes',
      b'---',
      b'name: uint16',
      b'type: integer',
      b'attributes:',
      b'  format: unsigned',
      b'  size: 2',
      b'  units: bytes',
      b'---',
      b'name: int32',
      b'type: integer',
      b'attributes:',
      b'  format: signed',
      b'  size: 4',
      b'  units: bytes',
      b'---',
      b'name: uint32',
      b'type: integer',
      b'attributes:',
      b'  format: unsigned',
      b'  size: 4',
      b'  units: bytes',
      b'---',
      b'name: uint64',
      b'type: integer',
      b'attributes:',
      b'  format: unsigned',
      b'  size: 8',
      b'  units: bytes',
      b'---',
      b'name: float32',
      b'type: floating-point',
      b'attributes:',
      b'  size: 4',
      b'  units: bytes',
      b'---',
      b'name: wchar16',
      b'type: character',
      b'attributes:',
      b'  size: 2',
      b'  units: bytes',
      b'---',
      b'name: dest_list_header',
      b'type: structure',
      b'attributes:',
      b'  byte_order: little-endian',
      b'members:',
      b'- name: format_version',
      b'  data_type: uint32',
      b'- name: number_of_entries',
      b'  data_type: uint32',
      b'- name: number_of_pinned_entries',
      b'  data_type: uint32',
      b'- name: unknown1',
      b'  data_type: float32',
      b'- name: last_entry_number',
      b'  data_type: uint32',
      b'- name: unknown2',
      b'  data_type: uint32',
      b'- name: last_revision_number',
      b'  data_type: uint32',
      b'- name: unknown3',
      b'  data_type: uint32',
      b'---',
      b'name: dest_list_entry_v1',
      b'type: structure',
      b'attributes:',
      b'  byte_order: little-endian',
      b'members:',
      b'- name: unknown1',
      b'  data_type: uint64',
      b'- name: droid_volume_identifier',
      b'  type: uuid',
      b'- name: droid_file_identifier',
      b'  type: uuid',
      b'- name: birth_droid_volume_identifier',
      b'  type: uuid',
      b'- name: birth_droid_file_identifier',
      b'  type: uuid',
      b'- name: hostname',
      b'  type: string',
      b'  encoding: ascii',
      b'  element_data_type: char',
      b'  elements_data_size: 16',
      b'- name: entry_number',
      b'  data_type: uint32',
      b'- name: unknown2',
      b'  data_type: uint32',
      b'- name: unknown3',
      b'  data_type: float32',
      b'- name: last_modification_time',
      b'  data_type: uint64',
      b'- name: pin_status',
      b'  data_type: int32',
      b'- name: path_size',
      b'  data_type: uint16',
      b'- name: path',
      b'  type: string',
      b'  encoding: utf-16-le',
      b'  element_data_type: wchar16',
      b'  number_of_elements: dest_list_entry_v1.path_size',
      b'---',
      b'name: dest_list_entry_v3',
      b'type: structure',
      b'attributes:',
      b'  byte_order: little-endian',
      b'members:',
      b'- name: unknown1',
      b'  data_type: uint64',
      b'- name: droid_volume_identifier',
      b'  type: uuid',
      b'- name: droid_file_identifier',
      b'  type: uuid',
      b'- name: birth_droid_volume_identifier',
      b'  type: uuid',
      b'- name: birth_droid_file_identifier',
      b'  type: uuid',
      b'- name: hostname',
      b'  type: string',
      b'  encoding: ascii',
      b'  element_data_type: char',
      b'  elements_data_size: 16',
      b'- name: entry_number',
      b'  data_type: uint32',
      b'- name: unknown2',
      b'  data_type: uint32',
      b'- name: unknown3',
      b'  data_type: float32',
      b'- name: last_modification_time',
      b'  data_type: uint64',
      b'- name: pin_status',
      b'  data_type: int32',
      b'- name: unknown4',
      b'  data_type: int32',
      b'- name: unknown5',
      b'  data_type: uint32',
      b'- name: unknown6',
      b'  data_type: uint64',
      b'- name: path_size',
      b'  data_type: uint16',
      b'- name: path',
      b'  type: string',
      b'  encoding: utf-16-le',
      b'  element_data_type: wchar16',
      b'  number_of_elements: dest_list_entry_v3.path_size',
      b'- name: unknown7',
      b'  data_type: uint32',
  ])

  _DATA_TYPE_FABRIC = dtfabric_fabric.DataTypeFabric(
      yaml_definition=_DATA_TYPE_FABRIC_DEFINITION)

  _DEST_LIST_HEADER = _DATA_TYPE_FABRIC.CreateDataTypeMap(u'dest_list_header')

  _DEST_LIST_HEADER_SIZE = _DEST_LIST_HEADER.GetByteSize()

  _DEST_LIST_ENTRY_V1 = _DATA_TYPE_FABRIC.CreateDataTypeMap(
      u'dest_list_entry_v1')

  _DEST_LIST_ENTRY_V3 = _DATA_TYPE_FABRIC.CreateDataTypeMap(
      u'dest_list_entry_v3')

  def __init__(self, debug=False, output_writer=None):
    """Initializes an Automatic Destinations Jump List file.

    Args:
      debug (Optional[bool]): True if debug information should be written.
      output_writer (Optional[OutputWriter]): output writer.
    """
    super(AutomaticDestinationsFile, self).__init__(
        debug=debug, output_writer=output_writer)
    self._format_version = None
    self.entries = []
    self.recovered_entries = []

  def _DebugPrintDestListEntry(self, dest_list_entry):
    """Prints DestList entry debug information.

    Args:
      dest_list_entry (dest_list_entry_v1|dest_list_entry_v3): DestList entry.
    """
    value_string = u'0x{0:08x}'.format(dest_list_entry.unknown1)
    self._DebugPrintValue(u'Unknown1', value_string)

    value_string = u'{0!s}'.format(dest_list_entry.droid_volume_identifier)
    self._DebugPrintValue(u'Droid volume identifier', value_string)

    value_string = u'{0!s}'.format(dest_list_entry.droid_file_identifier)
    self._DebugPrintValue(u'Droid file identifier', value_string)

    value_string = u'{0!s}'.format(
        dest_list_entry.birth_droid_volume_identifier)
    self._DebugPrintValue(u'Birth droid volume identifier', value_string)

    value_string = u'{0!s}'.format(dest_list_entry.birth_droid_file_identifier)
    self._DebugPrintValue(u'Birth droid file identifier', value_string)

    value_string, _, _ = dest_list_entry.hostname.partition(u'\x00')
    self._DebugPrintValue(u'Hostname', value_string)

    value_string = u'{0:d}'.format(dest_list_entry.entry_number)
    self._DebugPrintValue(u'Entry number', value_string)

    value_string = u'0x{0:08x}'.format(dest_list_entry.unknown2)
    self._DebugPrintValue(u'Unknown2', value_string)

    value_string = u'{0:f}'.format(dest_list_entry.unknown3)
    self._DebugPrintValue(u'Unknown3', value_string)

    value_string = FromFiletime(dest_list_entry.last_modification_time)
    value_string = u'{0!s}'.format(value_string)
    self._DebugPrintValue(u'Last modification time', value_string)

    # TODO: debug print pin status.
    value_string = u'{0:d}'.format(dest_list_entry.pin_status)
    self._DebugPrintValue(u'Pin status', value_string)

    if self._format_version >= 3:
      value_string = u'{0:d}'.format(dest_list_entry.unknown4)
      self._DebugPrintValue(u'Unknown4', value_string)

      value_string = u'0x{0:08x}'.format(dest_list_entry.unknown5)
      self._DebugPrintValue(u'Unknown5', value_string)

      value_string = u'0x{0:08x}'.format(dest_list_entry.unknown6)
      self._DebugPrintValue(u'Unknown6', value_string)

    value_string = u'{0:d} characters ({1:d} bytes)'.format(
        dest_list_entry.path_size, dest_list_entry.path_size * 2)
    self._DebugPrintValue(u'Path size', value_string)

    self._DebugPrintValue(u'Path string', dest_list_entry.path)

    if self._format_version >= 3:
      value_string = u'0x{0:08x}'.format(dest_list_entry.unknown7)
      self._DebugPrintValue(u'Unknown7', value_string)

    self._DebugPrintText(u'\n')

  def _DebugPrintDestListHeader(self, dest_list_header):
    """Prints DestList header debug information.

    Args:
      dest_list_header (dest_list_header): DestList header.
    """
    value_string = u'{0:d}'.format(dest_list_header.format_version)
    self._DebugPrintValue(u'Format version', value_string)

    value_string = u'{0:d}'.format(dest_list_header.number_of_entries)
    self._DebugPrintValue(u'Number of entries', value_string)

    value_string = u'{0:d}'.format(dest_list_header.number_of_pinned_entries)
    self._DebugPrintValue(u'Number of pinned entries', value_string)

    value_string = u'{0:f}'.format(dest_list_header.unknown1)
    self._DebugPrintValue(u'Unknown1', value_string)

    value_string = u'{0:d}'.format(dest_list_header.last_entry_number)
    self._DebugPrintValue(u'Last entry number', value_string)

    value_string = u'0x{0:08x}'.format(dest_list_header.unknown2)
    self._DebugPrintValue(u'Unknown2', value_string)

    value_string = u'{0:d}'.format(dest_list_header.last_revision_number)
    self._DebugPrintValue(u'Last revision number', value_string)

    value_string = u'0x{0:08x}'.format(dest_list_header.unknown3)
    self._DebugPrintValue(u'Unknown3', value_string)

    self._DebugPrintText(u'\n')

  def _ReadDestList(self, olecf_file):
    """Reads the DestList stream.

    Args:
      olecf_file (pyolecf.file): OLECF file.
    """
    olecf_item = olecf_file.root_item.get_sub_item_by_name(u'DestList')

    self._ReadDestListHeader(olecf_item)

    stream_offset = olecf_item.get_offset()
    stream_size = olecf_item.get_size()
    while stream_offset < stream_size:
      entry_size = self._ReadDestListEntry(olecf_item, stream_offset)
      stream_offset += entry_size

  def _ReadDestListEntry(self, olecf_item, stream_offset):
    """Reads a DestList stream entry.

    Args:
      olecf_item (pyolecf.item): OLECF item.
      stream_offset (int): stream offset of the entry.

    Returns:
      int: entry data size.
    """
    if self._format_version == 1:
      data_type_map = self._DEST_LIST_ENTRY_V1
      description = u'dest list entry v1'

    elif self._format_version >= 3:
      data_type_map = self._DEST_LIST_ENTRY_V3
      description = u'dest list entry v3'

    dest_list_entry, entry_data_size = self._ReadStructureWithSizeHint(
        olecf_item, stream_offset, data_type_map, description)

    if self._debug:
      self._DebugPrintDestListEntry(dest_list_entry)

    return entry_data_size

  def _ReadDestListHeader(self, olecf_item):
    """Reads the DestList stream header.

    Args:
      olecf_item (pyolecf.item): OLECF item.

    Raises:
      ParseError: if the DestList stream header cannot be read.
    """
    stream_offset = olecf_item.tell()
    dest_list_header = self._ReadStructure(
        olecf_item, stream_offset, self._DEST_LIST_HEADER_SIZE,
        self._DEST_LIST_HEADER, u'dest list header')

    if self._debug:
      self._DebugPrintDestListHeader(dest_list_header)

    if dest_list_header.format_version not in (1, 3, 4):
      raise errors.ParseError(u'Unsupported format version: {0:d}'.format(
          dest_list_header.format_version))

    self._format_version = dest_list_header.format_version

  def _ReadLNKFile(self, olecf_item):
    """Reads a LNK file.

    Args:
      olecf_item (pyolecf.item): OLECF item.

    Returns:
      LNKFileEntry: a LNK file entry.

    Raises:
      ParseError: if the LNK file cannot be read.
    """
    if self._debug:
      text = u'Reading LNK file from stream: {0:s}'.format(olecf_item.name)
      self._DebugPrintText(text)

    lnk_file_entry = LNKFileEntry(olecf_item.name)

    try:
      lnk_file_entry.Open(olecf_item)
    except IOError as exception:
      raise errors.ParseError((
          u'Unable to parse LNK file from stream: {0:s} '
          u'with error: {1:s}').format(olecf_item.name, exception))

    if self._debug:
      self._DebugPrintText(u'\n')

    return lnk_file_entry

  def _ReadLNKFiles(self, olecf_file):
    """Reads the LNK files.

    Args:
      olecf_file (pyolecf.file): OLECF file.
    """
    for olecf_item in olecf_file.root_item.sub_items:
      if olecf_item.name == u'DestList':
        continue

      lnk_file_entry = self._ReadLNKFile(olecf_item)
      if lnk_file_entry:
        self.entries.append(lnk_file_entry)

  def ReadFileObject(self, file_object):
    """Reads an Automatic Destinations Jump List file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    olecf_file = pyolecf.file()
    olecf_file.open_file_object(file_object)

    try:
      self._ReadDestList(olecf_file)
      self._ReadLNKFiles(olecf_file)

    finally:
      olecf_file.close()


class CustomDestinationsFile(data_format.BinaryDataFile):
  """Custom Destinations Jump List (.customDestinations-ms) file.

  Attributes:
    entries (list[LNKFileEntry]): LNK file entries.
    recovered_entries (list[LNKFileEntry]): recovered LNK file entries.
  """

  _DATA_TYPE_FABRIC_DEFINITION = b'\n'.join([
      b'name: byte',
      b'type: integer',
      b'attributes:',
      b'  size: 1',
      b'  units: bytes',
      b'---',
      b'name: uint16',
      b'type: integer',
      b'attributes:',
      b'  format: unsigned',
      b'  size: 2',
      b'  units: bytes',
      b'---',
      b'name: uint32',
      b'type: integer',
      b'attributes:',
      b'  format: unsigned',
      b'  size: 4',
      b'  units: bytes',
      b'---',
      b'name: wchar16',
      b'type: character',
      b'attributes:',
      b'  size: 2',
      b'  units: bytes',
      b'---',
      b'name: file_header',
      b'type: structure',
      b'attributes:',
      b'  byte_order: little-endian',
      b'members:',
      b'- name: unknown1',
      b'  data_type: uint32',
      b'- name: unknown2',
      b'  data_type: uint32',
      b'- name: unknown3',
      b'  data_type: uint32',
      b'- name: header_values_type',
      b'  data_type: uint32',
      b'---',
      b'name: file_header_value_type_0',
      b'type: structure',
      b'attributes:',
      b'  byte_order: little-endian',
      b'members:',
      b'- name: number_of_characters',
      b'  data_type: uint16',
      b'- name: value',
      b'  type: string',
      b'  encoding: utf-16-le',
      b'  element_data_type: wchar16',
      b'  number_of_elements: file_header_value_type0.number_of_characters',
      b'- name: number_of_entries',
      b'  data_type: uint32',
      b'---',
      b'name: file_header_value_type_1_or_2',
      b'type: structure',
      b'attributes:',
      b'  byte_order: little-endian',
      b'members:',
      b'- name: number_of_entries',
      b'  data_type: uint32',
      b'---',
      b'name: file_footer',
      b'type: structure',
      b'attributes:',
      b'  byte_order: little-endian',
      b'members:',
      b'- name: signature',
      b'  data_type: uint32',
      b'---',
      b'name: entry_header',
      b'type: structure',
      b'attributes:',
      b'  byte_order: little-endian',
      b'members:',
      b'- name: guid',
      b'  type: stream',
      b'  element_data_type: byte',
      b'  elements_data_size: 16',
  ])

  _DATA_TYPE_FABRIC = dtfabric_fabric.DataTypeFabric(
      yaml_definition=_DATA_TYPE_FABRIC_DEFINITION)

  _FILE_HEADER = _DATA_TYPE_FABRIC.CreateDataTypeMap(u'file_header')

  _FILE_HEADER_SIZE = _FILE_HEADER.GetByteSize()

  _HEADER_VALUE_TYPE_0 = _DATA_TYPE_FABRIC.CreateDataTypeMap(
      u'file_header_value_type_0')

  _HEADER_VALUE_TYPE_1_OR_2 = _DATA_TYPE_FABRIC.CreateDataTypeMap(
      u'file_header_value_type_1_or_2')

  _FILE_FOOTER = _DATA_TYPE_FABRIC.CreateDataTypeMap(u'file_footer')

  _FILE_FOOTER_SIZE = _FILE_FOOTER.GetByteSize()

  _FILE_FOOTER_SIGNATURE = 0xbabffbab

  _ENTRY_HEADER = _DATA_TYPE_FABRIC.CreateDataTypeMap(u'entry_header')

  _ENTRY_HEADER_SIZE = _ENTRY_HEADER.GetByteSize()

  _LNK_GUID = (
      b'\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46')

  def __init__(self, debug=False, output_writer=None):
    """Initializes a Custum Destinations Jump List file.

    Args:
      debug (Optional[bool]): True if debug information should be written.
      output_writer (Optional[OutputWriter]): output writer.
    """
    super(CustomDestinationsFile, self).__init__(
        debug=debug, output_writer=output_writer)
    self.entries = []
    self.recovered_entries = []

  def _DebugPrintFileFooter(self, file_footer):
    """Prints file footer debug information.

    Args:
      file_footer (file_footer): file footer.
    """
    value_string = u'0x{0:08x}'.format(file_footer.signature)
    self._DebugPrintValue(u'Signature', value_string)

    self._DebugPrintText(u'\n')

  def _DebugPrintFileHeader(self, file_header):
    """Prints file header debug information.

    Args:
      file_header (file_header): file header.
    """
    value_string = u'0x{0:08x}'.format(file_header.unknown1)
    self._DebugPrintValue(u'Unknown1', value_string)

    value_string = u'0x{0:08x}'.format(file_header.unknown2)
    self._DebugPrintValue(u'Unknown2', value_string)

    value_string = u'0x{0:08x}'.format(file_header.unknown3)
    self._DebugPrintValue(u'Unknown3', value_string)

    value_string = u'{0:d}'.format(file_header.header_values_type)
    self._DebugPrintValue(u'Header value type', value_string)

    self._DebugPrintText(u'\n')

  def _ReadFileHeader(self, file_object):
    """Reads the file header.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file header cannot be read.
    """
    file_offset = file_object.tell()
    file_header = self._ReadStructure(
        file_object, file_offset, self._FILE_HEADER_SIZE, self._FILE_HEADER,
        u'file header')

    if self._debug:
      self._DebugPrintFileHeader(file_header)

    if file_header.unknown1 != 2:
      raise errors.ParseError(u'Unsupported unknown1: {0:d}.'.format(
          file_header.unknown1))

    if file_header.header_values_type > 2:
      raise errors.ParseError(u'Unsupported header value type: {0:d}.'.format(
          file_header.header_values_type))

    if file_header.header_values_type == 0:
      data_type_map = self._HEADER_VALUE_TYPE_0
    else:
      data_type_map = self._HEADER_VALUE_TYPE_1_OR_2

    # TODO: implement read file_header_value_data for HEADER_VALUE_TYPE_0
    data_size = data_type_map.GetByteSize()
    file_header_value_data = file_object.read(data_size)

    try:
      file_header_value = data_type_map.MapByteStream(file_header_value_data)
    except dtfabric_errors.MappingError as exception:
      raise errors.ParseError(
          u'Unable to parse file header value with error: {0:s}'.format(
              exception))

    if self._debug:
      if file_header.header_values_type == 0:
        value_string = u'{0:d}'.format(file_header_value.number_of_characters)
        self._DebugPrintValue(u'Number of characters', value_string)

        # TODO: print string.

      value_string = u'{0:d}'.format(file_header_value.number_of_entries)
      self._DebugPrintValue(u'Number of entries', value_string)

      self._DebugPrintText(u'\n')

  def _ReadLNKFile(self, file_object):
    """Reads a LNK file.

    Args:
      file_object (file): file-like object.

    Returns:
      LNKFileEntry: a LNK file entry.

    Raises:
      ParseError: if the LNK file cannot be read.
    """
    file_offset = file_object.tell()
    if self._debug:
      self._DebugPrintText(
          u'Reading LNK file at offset: 0x{0:08x}\n'.format(file_offset))

    identifier = u'0x{0:08x}'.format(file_offset)
    lnk_file_entry = LNKFileEntry(identifier)

    try:
      lnk_file_entry.Open(file_object)
    except IOError as exception:
      raise errors.ParseError((
          u'Unable to parse LNK file at offset: 0x{0:08x} '
          u'with error: {1:s}').format(file_offset, exception))

    if self._debug:
      self._DebugPrintText(u'\n')

    return lnk_file_entry

  def _ReadLNKFiles(self, file_object):
    """Reads the LNK files.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the LNK files cannot be read.
    """
    file_offset = file_object.tell()
    remaining_file_size = self._file_size - file_offset

    # The Custom Destination file does not have a unique signature in
    # the file header that is why we use the first LNK class identifier (GUID)
    # as a signature.
    first_guid_checked = False
    while remaining_file_size > 4:
      try:
        entry_header = self._ReadStructure(
            file_object, file_offset, self._ENTRY_HEADER_SIZE,
            self._ENTRY_HEADER, u'entry header')

      except errors.ParseError as exception:
        error_message = (
            u'Unable to parse file entry header at offset: 0x{0:08x} '
            u'with error: {1:s}').format(file_offset, exception)

        if not first_guid_checked:
          raise errors.ParseError(error_message)

        logging.warning(error_message)
        break

      if entry_header.guid != self._LNK_GUID:
        error_message = u'Invalid entry header at offset: 0x{0:08x}.'.format(
            file_offset)

        if not first_guid_checked:
          raise errors.ParseError(error_message)

        file_object.seek(-16, os.SEEK_CUR)
        self._ReadFileFooter(file_object)

        file_object.seek(-4, os.SEEK_CUR)
        break

      first_guid_checked = True
      file_offset += 16
      remaining_file_size -= 16

      lnk_file_object = data_range.DataRange(
          file_object, data_offset=file_offset, data_size=remaining_file_size)

      lnk_file_entry = self._ReadLNKFile(lnk_file_object)
      if lnk_file_entry:
        self.entries.append(lnk_file_entry)

      file_offset += lnk_file_entry.data_size
      remaining_file_size -= lnk_file_entry.data_size

      file_object.seek(file_offset, os.SEEK_SET)

  def _ReadFileFooter(self, file_object):
    """Reads the file footer.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file footer cannot be read.
    """
    file_offset = file_object.tell()
    file_footer = self._ReadStructure(
        file_object, file_offset, self._FILE_FOOTER_SIZE, self._FILE_FOOTER,
        u'file footer')

    if self._debug:
      self._DebugPrintFileFooter(file_footer)

    if file_footer.signature != self._FILE_FOOTER_SIGNATURE:
      raise errors.ParseError(
          u'Invalid footer signature at offset: 0x{0:08x}.'.format(file_offset))

  def ReadFileObject(self, file_object):
    """Reads a Custom Destinations Jump List file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    self._ReadFileHeader(file_object)
    self._ReadLNKFiles(file_object)

    file_offset = file_object.tell()
    if file_offset < self._file_size - 4:
      # TODO: recover LNK files
      # * scan for LNK GUID and run _ReadLNKFiles on remaining data.
      if self._debug:
        self._DebugPrintText(u'Detected trailing data\n')
        self._DebugPrintText(u'\n')

    self._ReadFileFooter(file_object)