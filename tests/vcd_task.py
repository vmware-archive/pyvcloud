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

import os
import unittest
import yaml
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.task import Task
from pyvcloud.vcd.test import TestCase

class TestTask(TestCase):

    def test_0001_list_task(self):
        task_obj = Task(self.client)
        status_list = [TaskStatus.ERROR.value]
        records = task_obj.list_tasks(filter_status_list=status_list)
        n = len(list(records))
        self.logger.debug('found %s tasks' % n)
        assert n > 0


if __name__ == '__main__':
    unittest.main()
