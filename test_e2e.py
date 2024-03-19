#!/usr/bin/env python

import subprocess
import unittest
import os

class TestEndToEnd(unittest.TestCase):
    @staticmethod
    def read_file_as_string(file_path):
        # Determine the directory of the current script (test_e2e.py)
        current_script_directory = os.path.dirname(os.path.realpath(__file__))

        # Construct an absolute path by combining the script directory with the relative file path
        absolute_file_path = os.path.join(current_script_directory, file_path)

        with open(absolute_file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def test_update_regions_output(self):
        command = ["python", "update_regions.py", "--input-file", "./tests/fixtures/server_directory.csv", "--output-dir", "./tests/tmp", "--pretty"]
        _ = subprocess.run(command, capture_output=True, text=True)

        regions_xml_fixture = self.read_file_as_string('tests/fixtures/regions.xml')
        regions_xml_output = self.read_file_as_string('tests/tmp/regions.xml')
        self.assertEqual(regions_xml_fixture, regions_xml_output, "regions.xml should be identical")

        regions_xml_v3_fixture = self.read_file_as_string('tests/fixtures/regions-v3.xml')
        regions_xml_v3_output = self.read_file_as_string('tests/tmp/regions-v3.xml')
        self.assertEqual(regions_xml_v3_fixture, regions_xml_v3_output, "regions-v3.xml should be identical")

        regions_json_fixture = self.read_file_as_string('tests/fixtures/regions.json')
        regions_json_output = self.read_file_as_string('tests/tmp/regions.json')
        self.assertEqual(regions_json_fixture, regions_json_output, "regions.json should be identical")

        regions_json_v3_fixture = self.read_file_as_string('tests/fixtures/regions-v3.json')
        regions_json_v3_output = self.read_file_as_string('tests/tmp/regions-v3.json')
        self.assertEqual(regions_json_v3_fixture, regions_json_v3_output, "regions-v3.json should be identical")

# This allows the test to be run from the command line
if __name__ == '__main__':
    unittest.main()
