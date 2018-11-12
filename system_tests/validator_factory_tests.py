# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import os

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.vcd.validator_factory import ValidatorFactory
from pyvcloud.vcd.exceptions import InvalidParameterException


class TestValidatorFactory(BaseTestCase):

    def test_0010_length_validator(self):
        """LengthValidator test."""
        input = "1234"
        result = ValidatorFactory.length(0, 1).validate(input)

        self.assertEqual(result, None)

    def test_0010_length_validator_params(self):
        """LengthValidator params test."""
        input = "1234"

        try:
            ValidatorFactory.length(10, 9).validate(input)
        except InvalidParameterException as e:
            self.assertIsInstance(e, InvalidParameterException)

    def test_0030_pattern_validator(self):
        """PatternValidator test."""
        input = "http://someurl.com"
        result = ValidatorFactory.pattern(r'^((http|https)://)').validate(input)

        self.assertEqual(result, input)

    def test_0040_validate_folder_existence(self):
        """ValidateFolderExistence test."""
        input = os.getcwd()
        result = ValidatorFactory.checkForFolderExistence().validate(input)

        self.assertEqual(result, input)


if __name__ == '__main__':
    unittest.main()
