# -*- coding: utf-8 -*-
"""Tests for CUPS Internet Printing Protocol (IPP) files."""

from __future__ import unicode_literals

import unittest

from dtformats import cups_ipp

from tests import test_lib


class CupsIppFileTest(test_lib.BaseTestCase):
  """CUPS Internet Printing Protocol (IPP) file tests."""

  # pylint: disable=protected-access

  # TODO: test _FormatIntegerAsTagValue function

  # TODO: test _ReadAttribute function
  # TODO: test _ReadAttributesGroup function
  # TODO: test _ReadBooleanValue function
  # TODO: test _ReadDateTimeValue function
  # TODO: test _ReadIntegerValue function

  @test_lib.skipUnlessHasTestFile(['cups_ipp_2.0'])
  def testReadHeader(self):
    """Tests the _ReadHeader function."""
    output_writer = test_lib.TestOutputWriter()
    test_file = cups_ipp.CupsIppFile(output_writer=output_writer)

    test_file_path = self._GetTestFilePath(['cups_ipp_2.0'])
    with open(test_file_path, 'rb') as file_object:
      test_file._ReadHeader(file_object)

  @test_lib.skipUnlessHasTestFile(['cups_ipp_2.0'])
  def testReadFileObject(self):
    """Tests the ReadFileObject function."""
    output_writer = test_lib.TestOutputWriter()
    test_file = cups_ipp.CupsIppFile(
        debug=True, output_writer=output_writer)

    test_file_path = self._GetTestFilePath(['cups_ipp_2.0'])
    test_file.Open(test_file_path)


if __name__ == '__main__':
  unittest.main()
