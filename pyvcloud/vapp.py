# VMware vCloud Python SDK
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

# coding: utf-8

import requests
from schema.vcd.v1_5.schemas.vcloud import vAppType, vdcType, queryRecordViewType, taskType, vcloudType
from schema.vcd.v1_5.schemas.vcloud.vAppType import VAppType, NetworkConnectionSectionType
from iptools import ipv4, IpRange
from tabulate import tabulate
from helper import generalHelperFunctions as ghf

class VAPP(object):

    def __init__(self, vApp, headers):
        self.me = vApp
        self.headers = headers

    @property
    def name(self):
        return self.me.get_name()

    def details_of_vms(self):
        result = []
        children = self.me.get_Children()
        if children:
            vms = children.get_Vm()
            for vm in vms:
                name = vm.get_name()
                status = ghf.status[vm.get_status()]()
                owner = self.me.get_Owner().get_User().get_name()
                sections = vm.get_Section()
                virtualHardwareSection = filter(lambda section: section.__class__.__name__== "VirtualHardwareSection_Type", sections)[0]
                items = virtualHardwareSection.get_Item()
                cpu = filter(lambda item: item.get_Description().get_valueOf_() == "Number of Virtual CPUs", items)[0]
                cpu_capacity = cpu.get_ElementName().get_valueOf_().split(" virtual CPU(s)")[0]
                memory = filter(lambda item: item.get_Description().get_valueOf_() == "Memory Size", items)[0]
                memory_capacity = int(memory.get_ElementName().get_valueOf_().split(" MB of memory")[0]) / 1024
                operatingSystemSection = filter(lambda section: section.__class__.__name__== "OperatingSystemSection_Type", sections)[0]
                os = operatingSystemSection.get_Description().get_valueOf_()
                result.append([name, status, cpu_capacity + " vCPUs", str(memory_capacity) + " GB", os, owner])
        return result
        
    def execute(self, operation, blocking, failure_msg, http, output_json, body = None, targetVM = None):
        # get action link from vm or vapp that has the url of the desired operation
        if targetVM:
            link = filter(lambda link: link.get_rel() == operation, targetVM.get_Link())
        else:
            link = filter(lambda link: link.get_rel() == operation, self.me.get_Link())
        if not link:
            ghf.print_error("This " + self.name + " " + failure_msg, output_json)
        else:
            if http == "post":
                response = requests.post(link[0].get_href(), data = body, headers=self.headers)
            elif http == "put":
                response = requests.put(link[0].get_href(), data = body, headers=self.headers)
            else:
                response = requests.delete(link[0].get_href(), headers=self.headers)
            if response.status_code == requests.codes.accepted:
                task = taskType.parseString(response.content, True)
                # if blocking then display progress bar before outputing the result 
                if blocking:
                    ghf.display_progress(task, output_json, self.headers)
                # else display result immediately
                else:
                    if output_json:
                        print ghf.task_json(response.content)
                    else:
                        print ghf.task_table(response.content)
            else:
                # print the error message
                ghf.print_xml_error(response.content, output_json)        
        
    def deploy(self, blocking=True, output_json=True, powerOn='true'):
        # build the body for sending post request
        deployVAppParams = vcloudType.DeployVAppParamsType()
        # the valid values of on are true and false
        deployVAppParams.set_powerOn(powerOn)
        body = ghf.convertPythonObjToStr(deployVAppParams, name = "DeployVAppParams",
                                         namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5"')
        self.execute("deploy", blocking, "can't be deployed", "post", output_json, body)

    def undeploy(self, blocking=True, output_json=True, action='powerOff'):
        undeployVAppParams = vcloudType.UndeployVAppParamsType()
        # The valid values of action are powerOff (Power off the VMs. This is the default action if
        # this attribute is missing or empty), suspend (Suspend the VMs), shutdown (Shut down the VMs),
        # force (Attempt to power off the VMs. Failures in undeploying the VM or associated networks
        # are ignored. All references to the vApp and its VMs are removed from the database),
        # default (Use the actions, order, and delay specified in the StartupSection).
        undeployVAppParams.set_UndeployPowerAction(action)
        body = ghf.convertPythonObjToStr(undeployVAppParams, name = "UndeployVAppParams",
                                         namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5"')
        self.execute("undeploy", blocking, "can't be undeployed", "post", output_json, body)

    def reboot(self, blocking=True, output_json=True):
        self.execute("power:reboot", blocking, "can't be rebooted", "post", output_json)

    def poweron(self, blocking=True, output_json=True):
        self.execute("power:powerOn", blocking, "can't be powered on", "post", output_json)

    def poweroff(self, blocking=True, output_json=True):
        self.execute("power:powerOff", blocking, "can't be powered off", "post", output_json)

    def shutdown(self, blocking=True, output_json=True):
        self.execute("power:shutdown", blocking, "can't be shutdown", "post", output_json)

    def suspend(self, blocking=True, output_json=True):
        self.execute("power:suspend", blocking, "can't be suspended", "post", output_json)

    def reset(self, blocking=True, output_json=True):
        self.execute("power:reset", blocking, "can't be reset", "post", output_json)

    def delete(self, blocking=True, output_json=True):
        self.execute("remove", blocking, "can't be deleted", "delete", output_json)

    def create_snapshot(self, args):
        createSnapshotParams = vcloudType.CreateSnapshotParamsType()
        createSnapshotParams.set_name(args["--snapshot"])
        createSnapshotParams.set_memory(args["--memory"])
        createSnapshotParams.set_quiesce(args["--quiesce"])
        body = ghf.convertPythonObjToStr(createSnapshotParams, name = "CreateSnapshotParams",
                                         namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5"')
        self.execute("snapshot:create", args["--blocking"], "can't be taken a snapshot", "post", args["--json"], body)

    def revert_snapshot(self, args):
        self.execute("snapshot:revertToCurrent", args["--blocking"], "can't be reverted to its current snapshot", "post", args["--json"])

    def delete_snapshot(self, args):
        self.execute("snapshot:removeAll", args["--blocking"], "can't have its snapshot deleted", "post", args["--json"])
        
    # create instantiateVAppTemplateParams python object (read "vCloud API Programming Guide", pages 32 and 33)
    @staticmethod
    def create_instantiateVAppTemplateParams(name, template_href, deploy="true", power="true"):

        # template params that can be used as body of http request
        templateParams = vcloudType.InstantiateVAppTemplateParamsType()
        templateParams.set_name(name)
        templateParams.set_deploy(deploy)
        templateParams.set_powerOn(power)

        # set source of the templateParams using href of the template
        source = vcloudType.ReferenceType(href=template_href)
        templateParams.set_Source(source)
        templateParams.set_AllEULAsAccepted("true")

        return templateParams

    # this networkConfigSection is used to change the network connection of vapp
    @staticmethod
    def create_networkConfigSection(network_name, network_href, fence_mode):
        parentNetwork = vcloudType.ReferenceType(href=network_href)
        configuration = vcloudType.NetworkConfigurationType()
        configuration.set_ParentNetwork(parentNetwork)
        configuration.set_FenceMode(fence_mode)
        networkConfig = vcloudType.VAppNetworkConfigurationType()
        networkConfig.set_networkName(network_name)
        networkConfig.set_Configuration(configuration)
        info = vcloudType.Msg_Type()
        info.set_valueOf_("Configuration parameters for logical networks")
        networkConfigSection = vcloudType.NetworkConfigSectionType()
        networkConfigSection.add_NetworkConfig(networkConfig)
        networkConfigSection.set_Info(info)
        return networkConfigSection
        
    def connect_vms(self, network_name, ip_address_allocation_mode):
        children = self.me.get_Children()
        if children:
            vms = children.get_Vm()
            for vm in vms:
                networkConnectionSection = [section for section in vm.get_Section() if isinstance(section, NetworkConnectionSectionType)][0]
                for networkConnection in networkConnectionSection.get_NetworkConnection():
                    networkConnection.set_IpAddressAllocationMode(ip_address_allocation_mode)
                    networkConnection.set_network(network_name)
                    networkConnection.set_IsConnected('true')
                body = ghf.convertPythonObjToStr(networkConnectionSection, name = 'NetworkConnectionSection',
                                          namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmw="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"').\
                                          replace("vmw:Info", "ovf:Info")
                response = requests.put(vm.get_href() + "/networkConnectionSection/", data = body, headers=self.headers)
                if response.status_code == requests.codes.accepted:
                    task = taskType.parseString(response.content, True)
                    ghf.display_progress(task, False, self.headers)
                    task = taskType.parseString(response.content, True)
                    return (True, task)      
                else:
                    return (False, response.content)     
                    
    def disconnect_vms(self, network_name):
        pass 
                    
    def connect_to_network(self, network_name, network_href, fence_mode, output_json=True, blocking=True):
        # get link that contains url for sending http request to add a network
        # this link is located under NetworkConfigSection of the vapp
        vApp_NetworkConfigSection = [section for section in self.me.get_Section() if section.__class__.__name__ == "NetworkConfigSectionType"][0]
        link = [link for link in vApp_NetworkConfigSection.get_Link() if link.get_type() == "application/vnd.vmware.vcloud.networkConfigSection+xml"][0]
        # Now that we have the link for sending http requests, build the request body
        networkConfigSection = VAPP.create_networkConfigSection(network_name, network_href, fence_mode)
        # add the original networks to the networkConfigSection
        for networkConfig in vApp_NetworkConfigSection.get_NetworkConfig():
            if networkConfig.get_networkName().lower() == network_name.lower():
                ghf.print_error("This vapp is already connected to org vdc network " + network_name, output_json)
                return
            networkConfigSection.add_NetworkConfig(networkConfig)
        # need to be careful with replacing string because it might be wrong
        body = ghf.convertPythonObjToStr(networkConfigSection, name = 'NetworkConfigSection',
                                         namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"').\
                                         replace('Info msgid=""', "ovf:Info").replace("/Info", "/ovf:Info").replace("vmw:", "")
        response = requests.put(link.get_href(), data = body, headers = self.headers)
        if response.status_code == requests.codes.accepted:
            task = taskType.parseString(response.content, True)
            # if blocking then display progress bar before outputing the result 
            if blocking:
                ghf.display_progress(task, output_json, self.headers)
                task = taskType.parseString(response.content, True)
                return (True, task)
            # else display result immediately
            else:
                if output_json:
                    print ghf.task_json(response.content)
                else:
                    print ghf.task_table(response.content)
                return (False, response.content)
        else:
            # print the error message
            ghf.print_xml_error(response.content, output_json)

    # disconnect vapp from a network
    def disconnect_from_network(self, network_name, output_json=True, blocking=True):
        # get networkConfigSection of the vapp and remove the selected network
        networkConfigSection = [section for section in self.me.get_Section() if section.__class__.__name__ == "NetworkConfigSectionType"][0]
        link = [link for link in networkConfigSection.get_Link() if link.get_type() == "application/vnd.vmware.vcloud.networkConfigSection+xml"][0]
        # this is the index of the networkConfig to be removed from the networkConfigSection
        found = -1
        for index, networkConfig in enumerate(networkConfigSection.get_NetworkConfig()):
            if networkConfig.get_networkName().lower() == network_name.lower():
                found = index
        if found != -1:
            networkConfigSection.NetworkConfig.pop(found)
            # need to be careful with replacing string because it might be wrong
            body = ghf.convertPythonObjToStr(networkConfigSection, name = 'NetworkConfigSection',
                                             namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"').\
                                             replace("vmw:", "").replace('Info xmlns:vmw="http://www.vmware.com/vcloud/v1.5" msgid=""', "ovf:Info").\
                                             replace("/Info", "/ovf:Info")
            response = requests.put(link.get_href(), data = body, headers = self.headers)
            if response.status_code == requests.codes.accepted:
                task = taskType.parseString(response.content, True)
                # if blocking then display progress bar before outputing the result 
                if blocking:
                    ghf.display_progress(task, output_json, self.headers)
                # else display result immediately
                else:
                    if output_json:
                        print ghf.task_json(response.content)
                    else:
                        print ghf.task_table(response.content)
            else:
                # print the error message
                ghf.print_xml_error(response.content, output_json)
        else:
            ghf.print_error("No such network found in this vapp", output_json)        
            
    def attach_disk_to_vm(self, vm_name, disk_ref):
        children = self.me.get_Children()
        if children:            
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if vms:
                body = """
                 <DiskAttachOrDetachParams xmlns="http://www.vmware.com/vcloud/v1.5">
                     <Disk type="application/vnd.vmware.vcloud.disk+xml"
                         href="%s" />
                 </DiskAttachOrDetachParams>
                """ % disk_ref.href
                return self.execute("disk:attach", True, "can't be attached", "post", True, body=body, targetVM=vms[0])

    def detach_disk_from_vm(self, vm_name, disk_ref):
        children = self.me.get_Children()
        if children:            
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if vms:
                body = """
                 <DiskAttachOrDetachParams xmlns="http://www.vmware.com/vcloud/v1.5">
                     <Disk type="application/vnd.vmware.vcloud.disk+xml"
                         href="%s" />
                 </DiskAttachOrDetachParams>
                """ % disk_ref.href
                return self.execute("disk:detach", True, "can't be detached", "post", True, body=body, targetVM=vms[0])        
        
                        
