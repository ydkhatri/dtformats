# -*- coding: utf-8 -*-
"""MacOS keychain database files."""

from __future__ import unicode_literals

import collections

from dtfabric.runtime import data_maps as dtfabric_data_maps

from dtformats import data_format
from dtformats import errors


class KeychainDatabaseColumn(object):
  """MacOS keychain database column.

  Attributes:
    attribute_identifier (int): attribute identifier.
    attribute_name (str): attribute name.
  """

  def __init__(self):
    """Initializes a MacOS keychain database column."""
    super(KeychainDatabaseColumn, self).__init__()
    self.attribute_identifier = None
    self.attribute_name = None


class KeychainDatabaseTable(object):
  """MacOS keychain database table.

  Attributes:
    columns (list[KeychainDatabaseColumn]): columns.
    relation_identifier (int): relation identifier.
    relation_name (str): relation name.
  """

  def __init__(self):
    """Initializes a MacOS keychain database table."""
    super(KeychainDatabaseTable, self).__init__()
    self.columns = []
    self.relation_identifier = None
    self.relation_name = None


class KeychainDatabaseFile(data_format.BinaryDataFile):
  """MacOS keychain database file."""

  _DEFINITION_FILE = 'keychain.yaml'

  _FILE_SIGNATURE = b'kych'

  _RECORD_TYPE_CSSM_DL_DB_SCHEMA_INFO = 0x00000000
  _RECORD_TYPE_CSSM_DL_DB_SCHEMA_INDEXES = 0x00000001
  _RECORD_TYPE_CSSM_DL_DB_SCHEMA_ATTRIBUTES = 0x00000002

  _ATTRIBUTE_DATA_TYPES = {
      0: 'CSSM_DB_ATTRIBUTE_FORMAT_STRING',
      1: 'CSSM_DB_ATTRIBUTE_FORMAT_SINT32',
      2: 'CSSM_DB_ATTRIBUTE_FORMAT_UINT32',
      3: 'CSSM_DB_ATTRIBUTE_FORMAT_BIG_NUM',
      4: 'CSSM_DB_ATTRIBUTE_FORMAT_REAL',
      5: 'CSSM_DB_ATTRIBUTE_FORMAT_TIME_DATE',
      6: 'CSSM_DB_ATTRIBUTE_FORMAT_BLOB',
      7: 'CSSM_DB_ATTRIBUTE_FORMAT_MULTI_UINT32',
      8: 'CSSM_DB_ATTRIBUTE_FORMAT_COMPLEX'}

  def __init__(self, debug=False, output_writer=None):
    """Initializes a MacOS keychain database file.

    Args:
      debug (Optional[bool]): True if debug information should be written.
      output_writer (Optional[OutputWriter]): output writer.
    """
    super(KeychainDatabaseFile, self).__init__(
        debug=debug, output_writer=output_writer)
    self._tables = collections.OrderedDict()

  @property
  def tables(self):
    """list[KeychainDatabaseTable]: tables."""
    return self._tables.values()

  def _DebugPrintFileHeader(self, file_header):
    """Prints file header debug information.

    Args:
      file_header (keychain_file_header): file header.
    """
    value_string = file_header.signature.decode('ascii')
    self._DebugPrintValue('Signature', value_string)

    value_string = '{0:d}'.format(file_header.major_format_version)
    self._DebugPrintValue('Major format version', value_string)

    value_string = '{0:d}'.format(file_header.major_format_version)
    self._DebugPrintValue('Major format version', value_string)

    value_string = '{0:d}'.format(file_header.minor_format_version)
    self._DebugPrintValue('Minor format version', value_string)

    value_string = '{0:d}'.format(file_header.data_size)
    self._DebugPrintValue('Data size', value_string)

    value_string = '0x{0:08x}'.format(file_header.tables_array_offset)
    self._DebugPrintValue('Tables array offset', value_string)

    value_string = '0x{0:08x}'.format(file_header.unknown1)
    self._DebugPrintValue('Unknown1', value_string)

    self._DebugPrintText('\n')

  def _DebugPrintRecordHeader(self, record_header):
    """Prints record header debug information.

    Args:
      record_header (keychain_record_header): record header.
    """
    value_string = '{0:d}'.format(record_header.data_size)
    self._DebugPrintValue('Data size', value_string)

    value_string = '{0:d}'.format(record_header.record_index)
    self._DebugPrintValue('Record index', value_string)

    value_string = '0x{0:08x}'.format(record_header.unknown2)
    self._DebugPrintValue('Unknown2', value_string)

    value_string = '0x{0:08x}'.format(record_header.unknown3)
    self._DebugPrintValue('Unknown3', value_string)

    value_string = '0x{0:08x}'.format(record_header.unknown4)
    self._DebugPrintValue('Unknown4', value_string)

    value_string = '0x{0:08x}'.format(record_header.unknown5)
    self._DebugPrintValue('Unknown5', value_string)

    self._DebugPrintText('\n')

  def _DebugPrintTablesArray(self, tables_array):
    """Prints file tables array information.

    Args:
      tables_array (keychain_tables_array): tables array.
    """
    value_string = '{0:d}'.format(tables_array.data_size)
    self._DebugPrintValue('Data size', value_string)

    value_string = '{0:d}'.format(tables_array.number_of_tables)
    self._DebugPrintValue('Number of tables', value_string)

    for index, table_offset in enumerate(tables_array.table_offsets):
      description_string = 'Table offset: {0:d}'.format(index)
      value_string = '0x{0:08x}'.format(table_offset)
      self._DebugPrintValue(description_string, value_string)

    self._DebugPrintText('\n')

  def _DebugPrintTableHeader(self, table_header):
    """Prints table header debug information.

    Args:
      table_header (keychain_table_header): table header.
    """
    value_string = '{0:d}'.format(table_header.data_size)
    self._DebugPrintValue('Data size', value_string)

    value_string = '0x{0:08x}'.format(table_header.record_type)
    self._DebugPrintValue('Record type', value_string)

    value_string = '{0:d}'.format(table_header.number_of_records)
    self._DebugPrintValue('Number of records', value_string)

    value_string = '0x{0:08x}'.format(table_header.records_array_offset)
    self._DebugPrintValue('Records array offset', value_string)

    value_string = '0x{0:08x}'.format(table_header.unknown1)
    self._DebugPrintValue('Unknown1', value_string)

    value_string = '0x{0:08x}'.format(table_header.unknown2)
    self._DebugPrintValue('Unknown2', value_string)

    value_string = '{0:d}'.format(table_header.number_of_record_offsets)
    self._DebugPrintValue('Number of record offsets', value_string)

    for index, record_offset in enumerate(table_header.record_offsets):
      description_string = 'Record offset: {0:d}'.format(index)
      value_string = '0x{0:08x}'.format(record_offset)
      self._DebugPrintValue(description_string, value_string)

    self._DebugPrintText('\n')

  def _ReadAttributeValueInteger(
      self, attribute_values_data, record_offset, attribute_values_data_offset,
      attribute_value_offset, description):
    """Reads an integer attribute value.

    Args:
      attribute_values_data (bytes): attribute values data.
      record_offset (int): offset of the record relative to the start of
          the file.
      attribute_values_data_offset (int): offset of the attribute values data
          relative to the start of the record.
      attribute_value_offset (int): offset of the attribute relative to
          the start of the record.
      description (str): description of the attribute value.

    Returns:
      int: integer value or None if attribute value offset is not set.

    Raises:
      ParseError: if the attribute value cannot be read.
    """
    if attribute_value_offset == 0:
      return None

    data_type_map = self._GetDataTypeMap('uint32be')

    file_offset = (
        record_offset + attribute_values_data_offset + attribute_value_offset)

    attribute_value_offset -= attribute_values_data_offset + 1
    attribute_value_data = attribute_values_data[attribute_value_offset:]

    try:
      return self._ReadStructureFromByteStream(
          attribute_value_data, file_offset, data_type_map, description)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map integer attribute value data at offset: 0x{0:08x} '
          'with error: {1!s}').format(file_offset, exception))

  def _ReadAttributeValueString(
      self, attribute_values_data, record_offset, attribute_values_data_offset,
      attribute_value_offset, description):
    """Reads a string attribute value.

    Args:
      attribute_values_data (bytes): attribute values data.
      record_offset (int): offset of the record relative to the start of
          the file.
      attribute_values_data_offset (int): offset of the attribute values data
          relative to the start of the record.
      attribute_value_offset (int): offset of the attribute relative to
          the start of the record.
      description (str): description of the attribute value.

    Returns:
      str: string value or None if attribute value offset is not set.

    Raises:
      ParseError: if the attribute value cannot be read.
    """
    if attribute_value_offset == 0:
      return None

    data_type_map = self._GetDataTypeMap('keychain_string')

    file_offset = (
        record_offset + attribute_values_data_offset + attribute_value_offset)

    attribute_value_offset -= attribute_values_data_offset + 1
    attribute_value_data = attribute_values_data[attribute_value_offset:]

    try:
      string_attribute_value = self._ReadStructureFromByteStream(
          attribute_value_data, file_offset, data_type_map, description)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map string attribute value data at offset: 0x{0:08x} '
          'with error: {1!s}').format(file_offset, exception))

    return string_attribute_value.string

  def _ReadFileHeader(self, file_object):
    """Reads the file header.

    Args:
      file_object (file): file-like object.

    Returns:
      keychain_file_header: file header.

    Raises:
      ParseError: if the file header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('keychain_file_header')

    file_header, _ = self._ReadStructureFromFileObject(
        file_object, 0, data_type_map, 'file header')

    if self._debug:
      self._DebugPrintFileHeader(file_header)

    if file_header.signature != self._FILE_SIGNATURE:
      raise errors.ParseError('Unsupported file signature.')

    return file_header

  def _ReadRecord(self, file_object, record_offset):
    """Reads the record.

    Args:
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.

    Raises:
      ParseError: if the record cannot be read.
    """
    record_header = self._ReadRecordHeader(file_object, record_offset)

    if self._debug:
      record_data = file_object.read(record_header.data_size - 24)
      self._DebugPrintData('Record data', record_data)

  def _ReadRecordAttributeValueOffset(
      self, file_object, file_offset, number_of_attribute_values):
    """Reads the record attribute value offsets.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the record attribute values offsets relative
          to the start of the file.
      number_of_attribute_values (int): number of attribute values.

    Returns:
      keychain_record_attribute_value_offsets: record attribute value offsets.

    Raises:
      ParseError: if the record attribute value offsets cannot be read.
    """
    offsets_data_size = number_of_attribute_values * 4

    offsets_data = file_object.read(offsets_data_size)

    if self._debug:
      self._DebugPrintData('Attribute value offsets data', offsets_data)

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'number_of_attribute_values': number_of_attribute_values})

    data_type_map = self._GetDataTypeMap(
        'keychain_record_attribute_value_offsets')

    try:
      attribute_value_offsets = self._ReadStructureFromByteStream(
          offsets_data, file_offset, data_type_map,
          'record attribute value offsets', context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map record attribute value offsets data at offset: '
          '0x{0:08x} with error: {1!s}').format(file_offset, exception))

    if self._debug:
      for index, attribute_value_offset in enumerate(attribute_value_offsets):
        description_string = 'Attribute value offset: {0:d}'.format(index)
        value_string = '0x{0:08x}'.format(attribute_value_offset)
        self._DebugPrintValue(description_string, value_string)

      self._DebugPrintText('\n')

    return attribute_value_offsets

  def _ReadRecordHeader(self, file_object, record_header_offset):
    """Reads the record header.

    Args:
      file_object (file): file-like object.
      record_header_offset (int): offset of the record header relative to
          the start of the file.

    Returns:
      keychain_record_header: record header.

    Raises:
      ParseError: if the record header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('keychain_record_header')

    record_header, _ = self._ReadStructureFromFileObject(
        file_object, record_header_offset, data_type_map, 'record header')

    if self._debug:
      self._DebugPrintRecordHeader(record_header)

    return record_header

  def _ReadRecordSchemaAttributes(self, file_object, record_offset):
    """Reads a schema attributes (CSSM_DL_DB_SCHEMA_ATTRIBUTES) record.

    Args:
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.

    Raises:
      ParseError: if the record cannot be read.
    """
    record_header = self._ReadRecordHeader(file_object, record_offset)

    attribute_value_offsets = self._ReadRecordAttributeValueOffset(
        file_object, record_offset + 24, 6)

    file_offset = file_object.tell()
    attribute_values_data_offset = file_offset - record_offset
    attribute_values_data_size = record_header.data_size - (
        file_offset - record_offset)
    attribute_values_data = file_object.read(attribute_values_data_size)

    if self._debug:
      self._DebugPrintData('Attribute values data', attribute_values_data)

    relation_identifier = self._ReadAttributeValueInteger(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[0], 'relation identifier')

    if self._debug:
      if relation_identifier is None:
        value_string = 'NULL'
      else:
        value_string = '0x{0:08x}'.format(relation_identifier)
      self._DebugPrintValue('Relation identifier', value_string)

    attribute_identifier = self._ReadAttributeValueInteger(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[1], 'attribute identifier')

    if self._debug:
      if attribute_identifier is None:
        value_string = 'NULL'
      else:
        value_string = '{0:d}'.format(attribute_identifier)
      self._DebugPrintValue('Attribute identifier', value_string)

    attribute_name_data_type = self._ReadAttributeValueInteger(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[2], 'attribute name data type')

    if self._debug:
      if attribute_name_data_type is None:
        value_string = 'NULL'
      else:
        data_type_string = self._ATTRIBUTE_DATA_TYPES.get(
            attribute_name_data_type, 'UNKNOWN')
        value_string = '{0:d} ({1:s})'.format(
            attribute_name_data_type, data_type_string)
      self._DebugPrintValue('Attribute name data type', value_string)

    attribute_name = self._ReadAttributeValueString(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[3], 'attribute name')

    if self._debug:
      if attribute_name is None:
        value_string = 'NULL'
      else:
        value_string = attribute_name
      self._DebugPrintValue('Attribute name', value_string)

    # TODO: add support for AttributeNameID

    attribute_data_type = self._ReadAttributeValueInteger(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[5], 'attribute data type')

    if self._debug:
      if attribute_data_type is None:
        value_string = 'NULL'
      else:
        data_type_string = self._ATTRIBUTE_DATA_TYPES.get(
            attribute_data_type, 'UNKNOWN')
        value_string = '{0:d} ({1:s})'.format(
            attribute_data_type, data_type_string)
      self._DebugPrintValue('Attribute data type', value_string)

    if self._debug:
      self._DebugPrintText('\n')

    table = self._tables.get(relation_identifier, None)
    if not table:
      raise errors.ParseError(
          'Missing table for relation identifier: 0x{0:08}'.format(
              relation_identifier))

    # TODO: map attribute identifier to module specific names?
    if attribute_name is None and attribute_value_offsets[1] != 0:
      attribute_value_offset = attribute_value_offsets[1]
      attribute_value_offset -= attribute_values_data_offset + 1
      attribute_name = attribute_values_data[
          attribute_value_offset:attribute_value_offset + 4]
      attribute_name = attribute_name.decode('ascii')

    column = KeychainDatabaseColumn()
    column.attribute_identifier = attribute_identifier
    column.attribute_name = attribute_name

    table.columns.append(column)

  def _ReadRecordSchemaIndexes(self, file_object, record_offset):
    """Reads a schema indexes (CSSM_DL_DB_SCHEMA_INDEXES) record.

    Args:
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.

    Raises:
      ParseError: if the record cannot be read.
    """
    record_header = self._ReadRecordHeader(file_object, record_offset)

    attribute_value_offsets = self._ReadRecordAttributeValueOffset(
        file_object, record_offset + 24, 5)

    if attribute_value_offsets != (0x2d, 0x31, 0x35, 0x39, 0x3d):
      raise errors.ParseError('Unuspported record attribute value offsets')

    file_offset = file_object.tell()
    data_type_map = self._GetDataTypeMap('keychain_record_schema_indexes')

    record_values, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map,
        'schema indexes record values')

    if self._debug:
      value_string = '0x{0:08x}'.format(record_values.relation_identifier)
      self._DebugPrintValue('Relation identifier', value_string)

      value_string = '{0:d}'.format(record_values.index_identifier)
      self._DebugPrintValue('Index identifier', value_string)

      value_string = '0x{0:08x}'.format(record_values.attribute_identifier)
      self._DebugPrintValue('Attribute identifier', value_string)

    if record_values.relation_identifier not in self._tables:
      raise errors.ParseError(
          'CSSM_DL_DB_SCHEMA_INDEXES defines relation identifier not defined '
          'in CSSM_DL_DB_SCHEMA_INFO.')

    if self._debug:
      file_offset = file_object.tell()
      trailing_data_size = record_header.data_size - (
          file_offset - record_offset)

      if trailing_data_size == 0:
        self._DebugPrintText('\n')
      else:
        trailing_data = file_object.read(trailing_data_size)
        self._DebugPrintData('Record trailing data', trailing_data)

  def _ReadRecordSchemaInformation(self, file_object, record_offset):
    """Reads a schema information (CSSM_DL_DB_SCHEMA_INFO) record.

    Args:
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.

    Raises:
      ParseError: if the record cannot be read.
    """
    record_header = self._ReadRecordHeader(file_object, record_offset)

    attribute_value_offsets = self._ReadRecordAttributeValueOffset(
        file_object, record_offset + 24, 2)

    if attribute_value_offsets != (0x21, 0x25):
      raise errors.ParseError('Unuspported record attribute value offsets')

    file_offset = file_object.tell()
    data_type_map = self._GetDataTypeMap('keychain_record_schema_information')

    record_values, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map,
        'schema information record values')

    relation_name = record_values.relation_name.decode('ascii')

    if self._debug:
      value_string = '0x{0:08x}'.format(record_values.relation_identifier)
      self._DebugPrintValue('Relation identifier', value_string)

      value_string = '{0:d}'.format(record_values.relation_name_size)
      self._DebugPrintValue('Relation name size', value_string)

      self._DebugPrintValue('Relation name', relation_name)

    table = KeychainDatabaseTable()
    table.relation_identifier = record_values.relation_identifier
    table.relation_name = relation_name

    self._tables[table.relation_identifier] = table

    if self._debug:
      file_offset = file_object.tell()
      trailing_data_size = record_header.data_size - (
          file_offset - record_offset)

      if trailing_data_size == 0:
        self._DebugPrintText('\n')
      else:
        trailing_data = file_object.read(trailing_data_size)
        self._DebugPrintData('Record trailing data', trailing_data)

  def _ReadTablesArray(self, file_object, tables_array_offset):
    """Reads the tables array.

    Args:
      file_object (file): file-like object.
      tables_array_offset (int): offset of the tables array relative to
          the start of the file.

    Raises:
      ParseError: if the tables array cannot be read.
    """
    # TODO: implement https://github.com/libyal/dtfabric/issues/12 and update
    # keychain_tables_array definition.

    data_type_map = self._GetDataTypeMap('keychain_tables_array')

    tables_array, _ = self._ReadStructureFromFileObject(
        file_object, tables_array_offset, data_type_map, 'tables array')

    if self._debug:
      self._DebugPrintTablesArray(tables_array)

    for table_offset in tables_array.table_offsets:
      self._ReadTable(file_object, tables_array_offset + table_offset)

  def _ReadTable(self, file_object, table_offset):
    """Reads the table.

    Args:
      file_object (file): file-like object.
      table_offset (int): offset of the table relative to the start of
          the file.

    Raises:
      ParseError: if the table cannot be read.
    """
    table_header = self._ReadTableHeader(file_object, table_offset)

    for record_offset in table_header.record_offsets:
      if record_offset == 0:
        continue

      record_offset += table_offset

      if table_header.record_type == self._RECORD_TYPE_CSSM_DL_DB_SCHEMA_INFO:
        self._ReadRecordSchemaInformation(file_object, record_offset)
      elif table_header.record_type == (
          self._RECORD_TYPE_CSSM_DL_DB_SCHEMA_INDEXES):
        self._ReadRecordSchemaIndexes(file_object, record_offset)
      elif table_header.record_type == (
          self._RECORD_TYPE_CSSM_DL_DB_SCHEMA_ATTRIBUTES):
        self._ReadRecordSchemaAttributes(file_object, record_offset)
      else:
        self._ReadRecord(file_object, record_offset)

    if self._debug:
      file_offset = file_object.tell()
      trailing_data_size = table_header.data_size - (file_offset - table_offset)

      if trailing_data_size != 0:
        trailing_data = file_object.read(trailing_data_size)
        self._DebugPrintData('Table trailing data', trailing_data)

  def _ReadTableHeader(self, file_object, table_header_offset):
    """Reads the table header.

    Args:
      file_object (file): file-like object.
      tables_header_offset (int): offset of the tables header relative to
          the start of the file.

    Returns:
      keychain_table_header: table header.

    Raises:
      ParseError: if the table header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('keychain_table_header')

    table_header, _ = self._ReadStructureFromFileObject(
        file_object, table_header_offset, data_type_map, 'table header')

    if self._debug:
      self._DebugPrintTableHeader(table_header)

    return table_header

  def ReadFileObject(self, file_object):
    """Reads a MacOS keychain database file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    file_header = self._ReadFileHeader(file_object)

    self._ReadTablesArray(
        file_object, file_header.tables_array_offset)