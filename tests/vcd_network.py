# VMware vCloud Director Python SDK
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC


class TestNetwork(TestCase):
    def test_001_create_orgvdc_network(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))
        result = vdc.create_directly_connected_vdc_network(
            network_name=self.config['vcd']['vdc_direct_network_name'],
            description='Dummy description',
            parent_network_name=self.config['vcd']['ext_network_name'])
        task = self.client.get_task_monitor().wait_for_status(
                            task=result.Tasks.Task[0],
                            timeout=60,
                            poll_frequency=2,
                            fail_on_status=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value


if __name__ == '__main__':
    unittest.main()
