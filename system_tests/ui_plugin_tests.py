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

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.ui_plugin import UiPlugin
from pyvcloud.vcd.exceptions import InvalidParameterException


class TestUIPlugin(BaseTestCase):

    def test_0000_setup(self):
        # TODO(): need more pipeline work before this test can actually be run
        TestUIPlugin._client = Environment.get_sys_admin_client()
        TestUIPlugin._config = Environment.get_config()
        TestUIPlugin._vcd_host = self._config['vcd']['host']

    def test_0010_get_ui_extensions(self):
        """Get list of ui extensions."""
        ui = UiPlugin(TestUIPlugin._client)
        TestUIPlugin.ui_extensions = ui.getUiExtensions().json()

        self.assertIsInstance(TestUIPlugin.ui_extensions, list)

    def test_0020_get_ui_extension_by_id(self):
        """Get ui extension by id."""
        ui = UiPlugin(TestUIPlugin._client)
        ext = None

        if (len(TestUIPlugin.ui_extensions) > 0):
            ext = TestUIPlugin.ui_extensions[0]
            res = ui.getUiExtension(ext['id']).json()
            self.assertEqual(res['id'], ext['id'])
        else:
            try:
                res = ui.getUiExtension(ext).json()
            except InvalidParameterException as e:
                self.assertIsInstance(e, InvalidParameterException)

    def test_0030_delete_ui_extension(self):
        """Delete ui extension by id."""
        ui = UiPlugin(TestUIPlugin._client)
        ext = None

        if (len(TestUIPlugin.ui_extensions) > 0):
            ext = TestUIPlugin.ui_extensions[0]
            ui.delete(specific=ext['id'], deleteAll=False)
            after_delete_list = ui.getUiExtensions().json()
            self.assertEqual(len(after_delete_list), len(TestUIPlugin.ui_extensions) - 1)
        else:
            try:
                ui.delete(specific=ext, deleteAll=False)
            except Exception as e:
                self.assertIsInstance(e, Exception)

    def test_0040_delete_all_ui_extensions(self):
        """Delete all ui extensions."""
        ui = UiPlugin(TestUIPlugin._client)

        ui.delete(deleteAll=True)
        after_delete_list = ui.getUiExtensions().json()
        self.assertEqual(len(after_delete_list), 0)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestUIPlugin._client.logout()


if __name__ == '__main__':
    unittest.main()
