# VMware vCloud Director Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
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


from pyVim import connect
from pyVmomi import vim
import requests
import ssl
import time


class VSphere(object):

    def __init__(self, host, user, password, verify=True, port=443):
        self.host = host
        self.user = user
        self.password = password
        self.verify = verify
        self.port = port

    def connect(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        if not self.verify:
            context.verify_mode = ssl.CERT_NONE
        self.service_instance = connect.SmartConnect(host=self.host,
                                                     user=self.user,
                                                     pwd=self.password,
                                                     sslContext=context)

    def get_vm_by_moid(self, moid):
        vm = vim.VirtualMachine(moid)
        vm._stub = self.service_instance._stub
        return vm

    def execute_program_in_guest(self,
                                 vm,
                                 user,
                                 password,
                                 program_path,
                                 arguments,
                                 wait_for_completion=False,
                                 wait_time=1):
        creds = vim.vm.guest.NamePasswordAuthentication(username=user,
                                                        password=password)
        content = self.service_instance.RetrieveContent()
        pm = content.guestOperationsManager.processManager
        ps = vim.vm.guest.ProcessManager.ProgramSpec(
            programPath=program_path,
            arguments=arguments
        )
        result = pm.StartProgramInGuest(vm, creds, ps)
        if not wait_for_completion:
            return result
        while True:
            try:
                processes = pm.ListProcessesInGuest(vm, creds, [result])
                if processes[0].exitCode is not None:
                    return processes[0].exitCode
                else:
                    time.sleep(wait_time)
            except Exception:
                import traceback
                print(traceback.format_exc())
                print('will retry again in a few seconds')
                time.sleep(wait_time*3)

    def upload_file_to_guest(self,
                             vm,
                             user,
                             password,
                             data,
                             target_file):
        creds = vim.vm.guest.NamePasswordAuthentication(username=user,
                                                        password=password)
        content = self.service_instance.RetrieveContent()
        file_attribute = vim.vm.guest.FileManager.FileAttributes()
        url = content.guestOperationsManager.fileManager. \
            InitiateFileTransferToGuest(vm,
                                        creds,
                                        target_file,
                                        file_attribute,
                                        len(data),
                                        False)
        resp = requests.put(url, data=data, verify=False)
        if not resp.status_code == 200:
            raise Exception('Error while uploading file')
        else:
            return True

    def download_file_from_guest(self,
                                 vm,
                                 user,
                                 password,
                                 source_file):
        creds = vim.vm.guest.NamePasswordAuthentication(username=user,
                                                        password=password)
        content = self.service_instance.RetrieveContent()
        info = content.guestOperationsManager.fileManager. \
            InitiateFileTransferFromGuest(vm,
                                          creds,
                                          source_file)
        return requests.get(info.url, verify=False)
