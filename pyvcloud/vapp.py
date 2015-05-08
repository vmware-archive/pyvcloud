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
from StringIO import StringIO
from schema.vcd.v1_5.schemas.vcloud import vAppType, vdcType, queryRecordViewType, taskType, vcloudType
from schema.vcd.v1_5.schemas.vcloud.taskType import TaskType
from schema.vcd.v1_5.schemas.vcloud.vAppType import VAppType, NetworkConnectionSectionType
from iptools import ipv4, IpRange
from tabulate import tabulate
from pyvcloud.helper import CommonUtils


VCLOUD_STATUS_MAP = {
    -1: "Could not be created",
    0: "Unresolved",
    1: "Resolved",
    2: "Deployed",
    3: "Suspended",
    4: "Powered on",
    5: "Waiting for user input",
    6: "Unknown state",
    7: "Unrecognized state",
    8: "Powered off",
    9: "Inconsistent state",
    10: "Children do not all have the same status",
    11: "Upload initiated, OVF descriptor pending",
    12: "Upload initiated, copying contents",
    13: "Upload initiated , disk contents pending",
    14: "Upload has been quarantined",
    15: "Upload quarantine period has expired"
    }


class VAPP(object):

    def __init__(self, vApp, headers, verify):
        self.me = vApp
        self.headers = headers
        self.verify = verify
        self.response = None

    @property
    def name(self):
        return self.me.get_name()

    def execute(self, operation, http, body=None, targetVM=None):
        if targetVM:
            link = filter(lambda link: link.get_rel() == operation, targetVM.get_Link())
        else:
            link = filter(lambda link: link.get_rel() == operation, self.me.get_Link())
        if not link:
            print "unable to execute vApp operation: %s" % operation
            return False
        else:
            if http == "post":
                headers = self.headers
                if body and body.startswith('<DeployVAppParams '):
                    headers['Content-type'] = 'application/vnd.vmware.vcloud.deployVAppParams+xml'
                elif body and body.startswith('<UndeployVAppParams '):
                    headers['Content-type'] = 'application/vnd.vmware.vcloud.undeployVAppParams+xml'
                self.response = requests.post(link[0].get_href(), data = body, headers=headers, verify=self.verify)
            elif http == "put":
                self.response = requests.put(link[0].get_href(), data = body, headers=self.headers, verify=self.verify)
            else:
                self.response = requests.delete(link[0].get_href(), headers=self.headers, verify=self.verify)
            if self.response.status_code == requests.codes.accepted:
                return taskType.parseString(self.response.content, True)
            else:
                return False

    def deploy(self, powerOn=True):
        powerOnValue = 'true' if powerOn else 'false'
        deployVAppParams = vcloudType.DeployVAppParamsType()
        deployVAppParams.set_powerOn(powerOnValue)
        body = CommonUtils.convertPythonObjToStr(deployVAppParams, name = "DeployVAppParams",
                namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5"')
        return self.execute("deploy", "post", body=body)

    def undeploy(self, action='powerOff'):
        undeployVAppParams = vcloudType.UndeployVAppParamsType()
        # The valid values of action are powerOff (Power off the VMs. This is the default action if
        # this attribute is missing or empty), suspend (Suspend the VMs), shutdown (Shut down the VMs),
        # force (Attempt to power off the VMs. Failures in undeploying the VM or associated networks
        # are ignored. All references to the vApp and its VMs are removed from the database),
        # default (Use the actions, order, and delay specified in the StartupSection).
        undeployVAppParams.set_UndeployPowerAction(action)
        body = CommonUtils.convertPythonObjToStr(undeployVAppParams, name = "UndeployVAppParams",
                namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5"')
        return self.execute("undeploy", "post", body=body)

    def reboot(self):
        self.execute("power:reboot", "post")

    def poweron(self):
        return self.execute("power:powerOn", "post")

    def poweroff(self):
        return self.execute("power:powerOff", "post")

    def shutdown(self):
        return self.execute("power:shutdown", "post")

    def suspend(self):
        self.execute("power:suspend", "post")

    def reset(self):
        self.execute("power:reset", "post")

    def delete(self):
        return self.execute("remove", "delete")

    def create_snapshot(self, args):
        pass
        # createSnapshotParams = vcloudType.CreateSnapshotParamsType()
        # createSnapshotParams.set_name(args["--snapshot"])
        # createSnapshotParams.set_memory(args["--memory"])
        # createSnapshotParams.set_quiesce(args["--quiesce"])
        # body = ghf.convertPythonObjToStr(createSnapshotParams, name = "CreateSnapshotParams",
        #                                  namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5"')
        # self.execute("snapshot:create", args["--blocking"], "can't be taken a snapshot", "post", args["--json"], body)

    def revert_snapshot(self, args):
        pass
        # self.execute("snapshot:revertToCurrent", args["--blocking"], "can't be reverted to its current snapshot", "post", args["--json"])

    def delete_snapshot(self, args):
        pass
        # self.execute("snapshot:removeAll", args["--blocking"], "can't have its snapshot deleted", "post", args["--json"])

    @staticmethod
    def create_networkConfigSection(network_name, network_href, fence_mode):
        parentNetwork = vcloudType.ReferenceType(href=network_href, name=network_name)
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
        networkConfigSection.set_Info(vAppType.cimString(valueOf_="Network config"))
        return networkConfigSection

    def connect_vms(self, network_name, connection_index,
                    connections_primary_index=None, ip_allocation_mode='DHCP',
                    mac_address=None, ip_address=None):
        children = self.me.get_Children()
        if children:
            vms = children.get_Vm()
            for vm in vms:
                new_connection = self._create_networkConnection(
                    network_name, connection_index, ip_allocation_mode,
                    mac_address, ip_address)
                networkConnectionSection = [section for section in vm.get_Section() if isinstance(section, NetworkConnectionSectionType)][0]
                self._modify_networkConnectionSection(
                    networkConnectionSection,
                    new_connection,
                    connections_primary_index)
                output = StringIO()
                networkConnectionSection.export(output,
                    0,
                    name_ = 'NetworkConnectionSection',
                    namespacedef_ = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmw="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                    pretty_print = False)
                body=output.getvalue().replace("vmw:Info", "ovf:Info")
                self.response = requests.put(vm.get_href() + "/networkConnectionSection/", data=body, headers=self.headers, verify=self.verify)
                if self.response.status_code == requests.codes.accepted:
                    return taskType.parseString(self.response.content, True)

    def disconnect_vms(self, network_name):
        children = self.me.get_Children()
        if children:
            vms = children.get_Vm()
            for vm in vms:
                # print vm.get_Name()
                networkConnectionSection = [section for section in vm.get_Section() if isinstance(section, NetworkConnectionSectionType)][0]
                link = [link for link in networkConnectionSection.get_Link() if link.get_type() == "application/vnd.vmware.vcloud.networkConnectionSection+xml"][0]
                found = -1
                for index, networkConnection in enumerate(networkConnectionSection.NetworkConnection):
                       if networkConnection.get_network() == network_name:
                            found = index
                if found != -1:
                    networkConnectionSection.NetworkConnection.pop(found)
                    output = StringIO()
                    networkConnectionSection.export(output,
                    0,
                    name_ = 'NetworkConfigSection',
                    namespacedef_ = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                    pretty_print = False)
                    body = output.getvalue().\
                    replace("vmw:", "").replace('Info xmlns:vmw="http://www.vmware.com/vcloud/v1.5" msgid=""', "ovf:Info").\
                    replace("/Info", "/ovf:Info")
                    self.response = requests.put(link.get_href(), data=body, headers=self.headers, verify=self.verify)
                    if self.response.status_code == requests.codes.accepted:
                        return taskType.parseString(self.response.content, True)


    def connect_to_network(self, network_name, network_href, fence_mode='bridged'):
        vApp_NetworkConfigSection = [section for section in self.me.get_Section() if section.__class__.__name__ == "NetworkConfigSectionType"][0]
        link = [link for link in vApp_NetworkConfigSection.get_Link() if link.get_type() == "application/vnd.vmware.vcloud.networkConfigSection+xml"][0]
        networkConfigSection = VAPP.create_networkConfigSection(network_name, network_href, fence_mode)
        for networkConfig in vApp_NetworkConfigSection.get_NetworkConfig():
            if networkConfig.get_networkName() == network_name:
                task = TaskType()
                task.set_status("success")
                task.set_Progress("100")
                return task
            networkConfigSection.add_NetworkConfig(networkConfig)
        output = StringIO()
        networkConfigSection.export(output,
            0,
            name_ = 'NetworkConfigSection',
            namespacedef_ = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
            pretty_print = True)
        body = output.getvalue().\
            replace('Info msgid=""', "ovf:Info").replace("Info", "ovf:Info").replace(":vmw", "").replace("vmw:","")\
            .replace("RetainNetovf", "ovf").replace("ovf:InfoAcrossDeployments","RetainNetInfoAcrossDeployments")
        self.response = requests.put(link.get_href(), data=body, headers=self.headers, verify=self.verify)
        if self.response.status_code == requests.codes.accepted:
            return taskType.parseString(self.response.content, True)

    def disconnect_from_networks(self):
        networkConfigSection = [section for section in self.me.get_Section() if section.__class__.__name__ == "NetworkConfigSectionType"][0]
        link = [link for link in networkConfigSection.get_Link() if link.get_type() == "application/vnd.vmware.vcloud.networkConfigSection+xml"][0]
        networkConfigSection.NetworkConfig[:] = []
        output = StringIO()
        networkConfigSection.export(output,
            0,
            name_ = 'NetworkConfigSection',
            namespacedef_ = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
            pretty_print = False)
        body = output.getvalue().\
                replace("vmw:", "").replace('Info xmlns:vmw="http://www.vmware.com/vcloud/v1.5" msgid=""', "ovf:Info").\
                replace("/Info", "/ovf:Info")
        self.response = requests.put(link.get_href(), data=body, headers=self.headers, verify=self.verify)
        if self.response.status_code == requests.codes.accepted:
            return taskType.parseString(self.response.content, True)

    def disconnect_from_network(self, network_name):
        networkConfigSection = [section for section in self.me.get_Section() if section.__class__.__name__ == "NetworkConfigSectionType"][0]
        link = [link for link in networkConfigSection.get_Link() if link.get_type() == "application/vnd.vmware.vcloud.networkConfigSection+xml"][0]
        found = -1
        for index, networkConfig in enumerate(networkConfigSection.get_NetworkConfig()):
            if networkConfig.get_networkName() == network_name:
                found = index
        if found != -1:
            networkConfigSection.NetworkConfig.pop(found)
            output = StringIO()
            networkConfigSection.export(output,
                0,
                name_ = 'NetworkConfigSection',
                namespacedef_ = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                pretty_print = False)
            body = output.getvalue().\
                    replace("vmw:", "").replace('Info xmlns:vmw="http://www.vmware.com/vcloud/v1.5" msgid=""', "ovf:Info").\
                    replace("/Info", "/ovf:Info")
            self.response = requests.put(link.get_href(), data=body, headers=self.headers, verify=self.verify)
            if self.response.status_code == requests.codes.accepted:
                return taskType.parseString(self.response.content, True)

    def attach_disk_to_vm(self, vm_name, disk_ref):
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) ==1:
                body = """
                 <DiskAttachOrDetachParams xmlns="http://www.vmware.com/vcloud/v1.5">
                     <Disk type="application/vnd.vmware.vcloud.disk+xml"
                         href="%s" />
                 </DiskAttachOrDetachParams>
                """ % disk_ref.href
                return self.execute("disk:attach", "post", body=body, targetVM=vms[0])

    def detach_disk_from_vm(self, vm_name, disk_ref):
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) ==1:
                body = """
                 <DiskAttachOrDetachParams xmlns="http://www.vmware.com/vcloud/v1.5">
                     <Disk type="application/vnd.vmware.vcloud.disk+xml"
                         href="%s" />
                 </DiskAttachOrDetachParams>
                """ % disk_ref.href
                return self.execute("disk:detach", "post", body=body, targetVM=vms[0])

    def vm_media(self, vm_name, media, operation):
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) ==1:
                body = """
                 <MediaInsertOrEjectParams xmlns="http://www.vmware.com/vcloud/v1.5">
                     <Media
                       type="%s"
                       name="%s"
                       href="%s" />
                 </MediaInsertOrEjectParams>
                """ % (media.get('name'), media.get('id'), media.get('href'))
                return self.execute("media:%sMedia" % operation, "post", body=body, targetVM=vms[0])

    def customize_guest_os(self, vm_name, customization_script=None,
                           computer_name=None, admin_password=None,
                           reset_password_required=False):
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                sections = vms[0].get_Section()
                customization_section = [section for section in sections
                         if (section.__class__.__name__ ==
                             "GuestCustomizationSectionType")
                         ][0]
                customization_section.set_Enabled(True)
                customization_section.set_ResetPasswordRequired(
                    reset_password_required)
                customization_section.set_AdminAutoLogonEnabled(False)
                customization_section.set_AdminAutoLogonCount(0)
                if customization_script:
                    customization_section.set_CustomizationScript(
                        customization_script)
                if computer_name:
                    customization_section.set_ComputerName(computer_name)
                if admin_password:
                    customization_section.set_AdminPasswordEnabled(True)
                    customization_section.set_AdminPasswordAuto(False)
                    customization_section.set_AdminPassword(admin_password)
                output = StringIO()
                customization_section.export(output,
                    0,
                    name_ = 'GuestCustomizationSection',
                    namespacedef_ = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                    pretty_print = False)
                body = output.getvalue().\
                    replace("vmw:", "").replace('Info xmlns:vmw="http://www.vmware.com/vcloud/v1.5" msgid=""', "ovf:Info").\
                    replace("/Info", "/ovf:Info")
                headers = self.headers
                headers['Content-type'] = 'application/vnd.vmware.vcloud.guestcustomizationsection+xml'
                self.response = requests.put(customization_section.Link[0].href, data=body, headers=headers, verify=self.verify)
                if self.response.status_code == requests.codes.accepted:
                    return taskType.parseString(self.response.content, True)
                else:
                    print self.response.content


    def force_customization(self, vm_name):
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                sections = vms[0].get_Section()
                links = filter(lambda link: link.rel== "deploy", vms[0].Link)
                if len(links) == 1:
                    forceCustomizationValue = 'true'
                    deployVAppParams = vcloudType.DeployVAppParamsType()
                    deployVAppParams.set_powerOn('true')
                    deployVAppParams.set_deploymentLeaseSeconds(0)
                    deployVAppParams.set_forceCustomization('true')
                    body = CommonUtils.convertPythonObjToStr(deployVAppParams, name = "DeployVAppParams",
                            namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5"')
                    headers = self.headers
                    headers['Content-type'] = 'application/vnd.vmware.vcloud.deployVAppParams+xml'
                    self.response = requests.post(links[0].href, data=body, headers=headers, verify=self.verify)
                    if self.response.status_code == requests.codes.accepted:
                        return taskType.parseString(self.response.content, True)
                    else:
                        print self.response.content

    def get_vms_network_info(self):
        result = []
        vms = self._get_vms()
        for vm in vms:
            nw_connections = []
            sections = vm.get_Section()
            networkConnectionSection = filter(lambda section: section.__class__.__name__ == "NetworkConnectionSectionType", sections)[0]
            primary_index = networkConnectionSection.get_PrimaryNetworkConnectionIndex()
            connections = networkConnectionSection.get_NetworkConnection()
            for connection in connections:
                nw_connections.append(
                    {'network_name': connection.get_network(),
                     'ip': connection.get_IpAddress(),
                     'mac': connection.get_MACAddress(),
                     'is_connected': connection.get_IsConnected(),
                     'is_primary': connection.get_NetworkConnectionIndex() == primary_index,
                     'allocation_mode': connection.get_IpAddressAllocationMode()
                     })
            result.append(nw_connections)
        return result

    def customize_on_next_poweron(self):
        vm = self._get_vms()[0]
        link = filter(lambda link: link.get_rel() == "customizeAtNextPowerOn",
                      vm.get_Link())
        if link:
            self.response = requests.post(link[0].get_href(), data=None,
                                     headers=self.headers)
            if self.response.status_code == requests.codes.no_content:
                return True
        return False

    def get_vms_details(self):
        result = []
        children = self.me.get_Children()
        if children:
            vms = children.get_Vm()
            for vm in vms:
                name = vm.get_name()
                status = VCLOUD_STATUS_MAP[vm.get_status()]
                owner = self.me.get_Owner().get_User().get_name()
                sections = vm.get_Section()
                virtualHardwareSection = filter(lambda section: section.__class__.__name__== "VirtualHardwareSection_Type", sections)[0]
                items = virtualHardwareSection.get_Item()
                cpu = filter(lambda item: item.get_Description().get_valueOf_() == "Number of Virtual CPUs", items)[0]
                cpu_capacity = int(cpu.get_ElementName().get_valueOf_().split(" virtual CPU(s)")[0])
                memory = filter(lambda item: item.get_Description().get_valueOf_() == "Memory Size", items)[0]
                memory_capacity = int(memory.get_ElementName().get_valueOf_().split(" MB of memory")[0]) / 1024
                operatingSystemSection = filter(lambda section: section.__class__.__name__== "OperatingSystemSection_Type", sections)[0]
                os = operatingSystemSection.get_Description().get_valueOf_()
                result.append(
                    {'name': name,
                     'status': status,
                     'cpus': cpu_capacity,
                     'memory': memory_capacity,
                     'os': os,
                     'owner': owner}
                )
        return result

    def _get_vms(self):
        children = self.me.get_Children()
        if children:
            return children.get_Vm()
        else:
            return []

    def _modify_networkConnectionSection(self, section, new_connection,
                                         primary_index=None):

        #Need to add same interface more than once for a VM , so commenting out below lines

        # for networkConnection in section.get_NetworkConnection():
        #     if (networkConnection.get_network().lower() ==
        #         new_connection.get_network().lower()):
        #         return (False,
        #                 "VApp {0} is already connected to org vdc network {1}"
        #                 .format(self.name, networkConnection.get_network()))

        section.add_NetworkConnection(new_connection)
        if section.get_Info() is None:
            info = vcloudType.Msg_Type()
            info.set_valueOf_("Network connection")
            section.set_Info(info)
        if primary_index is not None:
            section.set_PrimaryNetworkConnectionIndex(primary_index)

    def _create_networkConnection(self, network_name, index, ip_allocation_mode,
                                  mac_address=None, ip_address=None):
        networkConnection = vcloudType.NetworkConnectionType()
        networkConnection.set_network(network_name)
        networkConnection.set_NetworkConnectionIndex(index)
        networkConnection.set_IpAddressAllocationMode(ip_allocation_mode)
        networkConnection.set_IsConnected(True)
        if ip_address and ip_allocation_mode == 'MANUAL':
            networkConnection.set_IpAddress(ip_address)
        if mac_address:
            networkConnection.set_MACAddress(mac_address)
        return networkConnection
