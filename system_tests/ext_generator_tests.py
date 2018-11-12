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
import shutil

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.ext_generator import ExtGenerator

def projectPromptsFn():
    return {
        'template_path': Environment.get_config()['vcd']['ui_extension_template_path'],
        'projectName': 'ui_plugin'
    }

def pluginPromptsFn(manifest):
    return {
        "urn": manifest["urn"],
        "name": manifest["name"],
        "containerVersion": manifest["containerVersion"],
        "version": manifest["version"],
        "scope": manifest["scope"],
        "permissions": manifest["permissions"],
        "description": manifest["description"],
        "vendor": manifest["vendor"],
        "license": manifest["license"],
        "link": manifest["link"],
        "module": manifest["module"],
        "route": manifest["route"]
    }


class TestExtGenerator(BaseTestCase):

    def test_0000_setup(self):
        TestExtGenerator.init_cwd = os.getcwd()
        TestExtGenerator.ext_gen_wdir = "%s/ext_generator_test_folder" % (TestExtGenerator.init_cwd)

        try:
            os.mkdir(TestExtGenerator.ext_gen_wdir)
        except FileExistsError:
            pass

    def test_0010_get_ui_extensions(self):
        """Generate ui extension."""
        os.chdir(TestExtGenerator.ext_gen_wdir)

        gen = ExtGenerator()
        gen.generate(projectPromptsFn, pluginPromptsFn)

        plugin_dist_dir = "%s/ui_plugin/dist" % (TestExtGenerator.ext_gen_wdir)

        self.assertTrue(os.path.exists("%s/manifest.json" % (plugin_dist_dir)))
        self.assertTrue(os.path.exists("%s/bundle.js" % (plugin_dist_dir)))

        os.chdir(TestExtGenerator.init_cwd)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        shutil.rmtree(TestExtGenerator.ext_gen_wdir)


if __name__ == '__main__':
    unittest.main()
