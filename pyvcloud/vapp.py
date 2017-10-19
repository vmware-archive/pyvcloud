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

import time
import requests
from StringIO import StringIO
from schema.vcd.v1_5.schemas.vcloud import vAppType, vdcType, queryRecordViewType, taskType, vcloudType
from schema.vcd.v1_5.schemas.vcloud.taskType import TaskType
from schema.vcd.v1_5.schemas.vcloud.vAppType import VAppType, NetworkConnectionSectionType
from pyvcloud.schema.vcim import errorType
from iptools import ipv4, IpRange
from pyvcloud.helper import CommonUtils
from pyvcloud import _get_logger, Http, Log
import copy

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

    def __init__(self, vApp, headers, verify, log=False):
        self.me = vApp
        self.headers = headers
        self.verify = verify
        self.response = None
        self.logger = _get_logger() if log else None

    @property
    def name(self):
        return self.me.get_name()

    def execute(self, operation, http, body=None, targetVM=None):
        """
        Execute an operation against a VM as an Asychronous Task.

        :param operation: (str): The command to execute
        :param http: (str): The http operation.
        :param body: (str, optional): a body for the http request
        :param targetVM: (str, optional): The name of the VM that will be the target of the request.
        :return: (TaskType or Bool) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request. \n
                Or False if the request failed, error and debug level messages are logged.

        """
        vApp = targetVM if targetVM else self.me
        link = filter(lambda link: link.get_rel()
                      == operation, vApp.get_Link())
        if not link:
            Log.error(self.logger, "link not found; rel=%s" % operation)
            Log.debug(
                self.logger, "vApp href=%s, name=%s" %
                (vApp.get_href(), vApp.get_name()))
            return False
        else:
            if http == "post":
                headers = self.headers
                if body and body.startswith('<DeployVAppParams '):
                    headers[
                        'Content-type'] = 'application/vnd.vmware.vcloud.deployVAppParams+xml'
                elif body and body.startswith('<UndeployVAppParams '):
                    headers[
                        'Content-type'] = 'application/vnd.vmware.vcloud.undeployVAppParams+xml'
                elif body and body.startswith('<CreateSnapshotParams '):
                    headers[
                        'Content-type'] = 'application/vnd.vmware.vcloud.createSnapshotParams+xml'
                self.response = Http.post(
                    link[0].get_href(),
                    data=body,
                    headers=headers,
                    verify=self.verify,
                    logger=self.logger)
            elif http == "put":
                self.response = Http.put(
                    link[0].get_href(),
                    data=body,
                    headers=self.headers,
                    verify=self.verify,
                    logger=self.logger)
            else:
                self.response = Http.delete(
                    link[0].get_href(),
                    headers=self.headers,
                    verify=self.verify,
                    logger=self.logger)
            if self.response.status_code == requests.codes.accepted:
                return taskType.parseString(self.response.content, True)
            else:
                Log.debug(
                    self.logger, "failed; response status=%d, content=%s" %
                    (self.response.status_code, self.response.text))
                return False

    def deploy(self, powerOn=True, targetVM=None):
        """
        Deploy the vapp

        :param powerOn: (bool, optional): Power on the vApp and its contained VMs after deployment.
        :return: (bool): True if the user was vApp was successfully deployed, False otherwise.

        """
        powerOnValue = 'true' if powerOn else 'false'
        deployVAppParams = vcloudType.DeployVAppParamsType()
        deployVAppParams.set_powerOn(powerOnValue)
        body = CommonUtils.convertPythonObjToStr(
            deployVAppParams,
            name="DeployVAppParams",
            namespacedef='xmlns="http://www.vmware.com/vcloud/v1.5"')
        return self.execute("deploy", "post", body=body, targetVM=targetVM)

    def undeploy(self, action='powerOff', targetVM=None):
        """
        Undeploy the vapp

        :param action: (bool, optional): Power off the vApp and its contained VMs or VM after undeployment.

                                       *  The valid values of action are

                                       -  **powerOff** (Power off the VMs. This is the default action if
                                          this attribute is missing or empty),

                                       -  **suspend** (Suspend the VMs), shutdown (Shut down the VMs),

                                       -  **force** (Attempt to power off the VMs. Failures in undeploying the VM or associated networks
                                          are ignored. All references to the vApp and its VMs are removed from the database),

                                       -  **default** (Use the actions, order, and delay specified in the StartupSection).

        :returns: (bool): True if the vApp or VM was successfully undeployed, False otherwise.

        """
        undeployVAppParams = vcloudType.UndeployVAppParamsType()

        undeployVAppParams.set_UndeployPowerAction(action)
        body = CommonUtils.convertPythonObjToStr(
            undeployVAppParams,
            name="UndeployVAppParams",
            namespacedef='xmlns="http://www.vmware.com/vcloud/v1.5"')
        return self.execute("undeploy", "post", body=body, targetVM=targetVM)

    def reboot(self):
        """
        Reboot the vApp
        :returns: (None)
        """
        self.execute("power:reboot", "post")

    def poweron(self):
        """
        Power on the vApp
        :returns: (None)
        """
        return self.execute("power:powerOn", "post")

    def poweroff(self):
        """
        Power off the vApp
        :returns: (None)
        """
        return self.execute("power:powerOff", "post")

    def shutdown(self):
        """
        Shutdown the vApp
        :returns: (None)
        """
        return self.execute("power:shutdown", "post")

    def suspend(self):
        """
        Suspend the vApp
        :returns: (None)
        """
        self.execute("power:suspend", "post")

    def reset(self):
        """
        Reset the vApp
        :returns: (None)
        """
        self.execute("power:reset", "post")

    def delete(self):
        """
        Delete the vApp

        Note: The vApp must be undeployed and power it off before it is deleted.

        :returns: (None)
        """
        return self.execute("remove", "delete")

    def create_snapshot(self):
        """
        Create a new snapshot of the vApp state.

        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.

        """
        snapshot_name = '{}_snapshot_{}'.format(
            self.name, int(round(time.time() * 1000)))
        createSnapshotParams = vcloudType.CreateSnapshotParamsType()
        createSnapshotParams.set_name(snapshot_name)
        createSnapshotParams.set_Description(snapshot_name)
        body = CommonUtils.convertPythonObjToStr(
            createSnapshotParams,
            name="CreateSnapshotParams",
            namespacedef='xmlns="http://www.vmware.com/vcloud/v1.5"')
        return self.execute("snapshot:create", "post", body)

    def revert_snapshot(self):
        """
        Revert to a previous vApp snapshot.

        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.

        """
        return self.execute("snapshot:revertToCurrent", "post")

    def delete_snapshot(self):
        """
        Delete an existing snapshot.

        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.

        """
        return self.execute("snapshot:removeAll", "post")

    @staticmethod
    def create_networkConfigSection(
            network_name,
            network_href,
            fence_mode,
            prev_network_config_section=None):
        parentNetwork = vcloudType.ReferenceType(
            href=network_href, name=network_name)
        configuration = vcloudType.NetworkConfigurationType()
        configuration.set_ParentNetwork(parentNetwork)
        configuration.set_FenceMode(fence_mode)
        networkConfig = vcloudType.VAppNetworkConfigurationType()
        networkConfig.set_networkName(network_name)
        networkConfig.set_Configuration(configuration)
        info = vcloudType.Msg_Type()
        info.set_valueOf_("Configuration parameters for logical networks")
        networkConfigSection = None
        if prev_network_config_section is None:
            networkConfigSection = vcloudType.NetworkConfigSectionType()
        else:
            networkConfigSection = prev_network_config_section
        networkConfigSection.add_NetworkConfig(networkConfig)
        networkConfigSection.set_Info(
            vAppType.cimString(
                valueOf_="Network config"))
        return networkConfigSection

    def connect_vms(self, network_name, connection_index,
                    connections_primary_index=None, ip_allocation_mode='DHCP',
                    mac_address=None, ip_address=None):
        """
        Attach vms to a virtual network.

        something helpful.

        :param network_name: (str): The network name to connect the VM to.
        :param connection_index: (str): Virtual slot number associated with this NIC. First slot number is 0.
        :param connections_primary_index: (str): Virtual slot number associated with the NIC that should be considered this \n
                  virtual machine's primary network connection. Defaults to slot 0.
        :param ip_allocation_mode: (str, optional): IP address allocation mode for this connection.

                                 * One of:

                                  - POOL (A static IP address is allocated automatically from a pool of addresses.)

                                  - DHCP (The IP address is obtained from a DHCP service.)

                                  - MANUAL (The IP address is assigned manually in the IpAddress element.)

                                  - NONE (No IP addressing mode specified.)

        :param mac_address: (str):    the MAC address associated with the NIC.
        :param ip_address: (str):     the IP address assigned to this NIC.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.


        """
        children = self.me.get_Children()
        if children:
            vms = children.get_Vm()
            for vm in vms:
                new_connection = self._create_networkConnection(
                    network_name, connection_index, ip_allocation_mode,
                    mac_address, ip_address)
                networkConnectionSection = [
                    section for section in vm.get_Section() if isinstance(
                        section, NetworkConnectionSectionType)][0]
                self._modify_networkConnectionSection(
                    networkConnectionSection,
                    new_connection,
                    connections_primary_index)
                output = StringIO()
                networkConnectionSection.export(
                    output,
                    0,
                    name_='NetworkConnectionSection',
                    namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmw="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                    pretty_print=True)
                body = output.getvalue().replace("vmw:Info", "ovf:Info")
                self.response = Http.put(
                    vm.get_href() +
                    "/networkConnectionSection/",
                    data=body,
                    headers=self.headers,
                    verify=self.verify,
                    logger=self.logger)
                if self.response.status_code == requests.codes.accepted:
                    return taskType.parseString(self.response.content, True)

    def connect_vm(self, vm_name, network_name, connection_index,
                   connections_primary_index=None, ip_allocation_mode='DHCP',
                   mac_address=None, ip_address=None):
        """
        Attach a single vm to a virtual network.

        :param vm_name: (str): The name of the vm that the network will be attached to.
        :param network_name: (str): The network name to connect the VM to.
        :param connection_index: (str): Virtual slot number associated with this NIC. First slot number is 0.
        :param connections_primary_index: (str): Virtual slot number associated with the NIC that should be considered this \n
                  virtual machine's primary network connection. Defaults to slot 0.
        :param ip_allocation_mode: (str, optional): IP address allocation mode for this connection.

                                 * One of:

                                  - POOL (A static IP address is allocated automatically from a pool of addresses.)

                                  - DHCP (The IP address is obtained from a DHCP service.)

                                  - MANUAL (The IP address is assigned manually in the IpAddress element.)

                                  - NONE (No IP addressing mode specified.)

        :param mac_address: (str):    the MAC address associated with the NIC.
        :param ip_address: (str):     the IP address assigned to this NIC.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.
        :raises: Exception: If the named VM cannot be located or another error occured.


        """
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                vm = vms[0]

                new_connection = self._create_networkConnection(
                    network_name, connection_index, ip_allocation_mode,
                    mac_address, ip_address)
                networkConnectionSection = [
                    section for section in vm.get_Section() if isinstance(
                        section, NetworkConnectionSectionType)][0]
                self._modify_networkConnectionSection(
                    networkConnectionSection,
                    new_connection,
                    connections_primary_index)
                output = StringIO()
                networkConnectionSection.export(
                    output,
                    0,
                    name_='NetworkConnectionSection',
                    namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmw="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                    pretty_print=True)
                link = filter(
                    lambda link: link.get_rel() == 'edit',
                    networkConnectionSection.get_Link())
                body = output.getvalue().replace("vmw:Info", "ovf:Info")
                headers = self.headers
                headers['Content-type'] = link[0].get_type()
                self.response = Http.put(
                    link[0].get_href(),
                    data=body,
                    headers=headers,
                    verify=self.verify,
                    logger=self.logger)
                if self.response.status_code == requests.codes.accepted:
                    return taskType.parseString(self.response.content, True)
                else:
                    raise Exception(self.response.status_code)

        raise Exception('can\'t find vm')

    def disconnect_vms(self, network_name=None):
        """
        Disconnect the vm from the vapp network.

        :param network_name: (string): The name of the vApp network. If None, then disconnect from all the networks.
        :return: (bool): True if the user was vApp was successfully deployed, False otherwise.

        """
        children = self.me.get_Children()
        if children:
            vms = children.get_Vm()
            for vm in vms:
                Log.debug(self.logger, "child VM name=%s" % vm.get_name())
                networkConnectionSection = [
                    section for section in vm.get_Section() if isinstance(
                        section, NetworkConnectionSectionType)][0]
                found = -1
                if network_name is None:
                    networkConnectionSection.set_NetworkConnection([])
                    found = 1
                else:
                    for index, networkConnection in enumerate(
                            networkConnectionSection.get_NetworkConnection()):
                        if networkConnection.get_network() == network_name:
                            found = index
                            break
                    if found != -1:
                        networkConnectionSection.NetworkConnection.pop(found)
                if found != -1:
                    output = StringIO()
                    networkConnectionSection.export(
                        output,
                        0,
                        name_='NetworkConnectionSection',
                        namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmw="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                        pretty_print=True)
                    body = output.getvalue().replace("vmw:Info", "ovf:Info")
                    self.response = Http.put(
                        vm.get_href() +
                        "/networkConnectionSection/",
                        data=body,
                        headers=self.headers,
                        verify=self.verify,
                        logger=self.logger)
                    if self.response.status_code == requests.codes.accepted:
                        return taskType.parseString(
                            self.response.content, True)
        task = TaskType()
        task.set_status("success")
        task.set_Progress("100")
        return task

    def disconnect_vm(self, vm_name, network_name=None):
        """
        Disconnect the vm from the vapp network.

        :param vm_name: (str): The name of the vm that the network will be disconnected from.
        :param network_name: (string): The name of the vApp network. If None, then disconnect from all the networks.
        :return: (bool): True if the user was vApp was successfully deployed, False otherwise.

        """
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                vm = vms[0]

                Log.debug(self.logger, "child VM name=%s" % vm.get_name())
                networkConnectionSection = [
                    section for section in vm.get_Section() if isinstance(
                        section, NetworkConnectionSectionType)][0]
                found = -1
                if network_name is None:
                    networkConnectionSection.set_NetworkConnection([])
                    found = 1
                else:
                    for index, networkConnection in enumerate(
                            networkConnectionSection.get_NetworkConnection()):
                        if networkConnection.get_network() == network_name:
                            found = index
                            break
                    if found != -1:
                        networkConnectionSection.NetworkConnection.pop(found)
                if found != -1:
                    output = StringIO()
                    networkConnectionSection.export(
                        output,
                        0,
                        name_='NetworkConnectionSection',
                        namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmw="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                        pretty_print=True)
                    body = output.getvalue().replace("vmw:Info", "ovf:Info")
                    self.response = Http.put(
                        vm.get_href() +
                        "/networkConnectionSection/",
                        data=body,
                        headers=self.headers,
                        verify=self.verify,
                        logger=self.logger)
                    if self.response.status_code == requests.codes.accepted:
                        return taskType.parseString(
                            self.response.content, True)
        task = TaskType()
        task.set_status("success")
        task.set_Progress("100")
        return task

    def connect_to_network(
            self,
            network_name,
            network_href,
            fence_mode='bridged'):
        """
        Connect the vApp to an existing virtual network in the VDC.

        :param network_name: (str): The name of the virtual network.
        :param network_href: (str): A uri that points to the network resource.
        :param fence_mode: (str, optional):
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.

        """
        vApp_NetworkConfigSection = [section for section in self.me.get_Section(
        ) if section.__class__.__name__ == "NetworkConfigSectionType"][0]
        link = [link for link in vApp_NetworkConfigSection.get_Link() if link.get_type(
        ) == "application/vnd.vmware.vcloud.networkConfigSection+xml"][0]
        for networkConfig in vApp_NetworkConfigSection.get_NetworkConfig():
            if networkConfig.get_networkName() == network_name:
                task = TaskType()
                task.set_status("success")
                task.set_Progress("100")
                return task
        networkConfigSection = VAPP.create_networkConfigSection(
            network_name, network_href, fence_mode, vApp_NetworkConfigSection)
        output = StringIO()
        networkConfigSection.export(
            output,
            0,
            name_='NetworkConfigSection',
            namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
            pretty_print=True)
        body = output.getvalue(). replace(
            'Info msgid=""',
            "ovf:Info").replace(
            "Info",
            "ovf:Info").replace(
            ":vmw",
            "").replace(
                "vmw:",
                "") .replace(
                    "RetainNetovf",
                    "ovf").replace(
                        "ovf:InfoAcrossDeployments",
            "RetainNetInfoAcrossDeployments")
        self.response = Http.put(
            link.get_href(),
            data=body,
            headers=self.headers,
            verify=self.verify,
            logger=self.logger)
        if self.response.status_code == requests.codes.accepted:
            return taskType.parseString(self.response.content, True)

    def disconnect_from_networks(self):
        """
        Disconnect the vApp from currently connected virtual networks.

        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.

        """
        networkConfigSection = [section for section in self.me.get_Section(
        ) if section.__class__.__name__ == "NetworkConfigSectionType"][0]
        link = [link for link in networkConfigSection.get_Link() if link.get_type(
        ) == "application/vnd.vmware.vcloud.networkConfigSection+xml"][0]
        networkConfigSection.NetworkConfig[:] = []
        output = StringIO()
        networkConfigSection.export(
            output,
            0,
            name_='NetworkConfigSection',
            namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
            pretty_print=True)
        body = output.getvalue(). replace(
            "vmw:",
            "").replace(
            'Info xmlns:vmw="http://www.vmware.com/vcloud/v1.5" msgid=""',
            "ovf:Info"). replace(
            "/Info",
            "/ovf:Info")
        self.response = Http.put(
            link.get_href(),
            data=body,
            headers=self.headers,
            verify=self.verify,
            logger=self.logger)
        if self.response.status_code == requests.codes.accepted:
            return taskType.parseString(self.response.content, True)

    def disconnect_from_network(self, network_name):
        """
        Disconnect the vApp from an existing virtual network in the VDC.

        :param network_name: (str): The name of the virtual network.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.

        """

        networkConfigSection = [section for section in self.me.get_Section(
        ) if section.__class__.__name__ == "NetworkConfigSectionType"][0]
        link = [link for link in networkConfigSection.get_Link() if link.get_type(
        ) == "application/vnd.vmware.vcloud.networkConfigSection+xml"][0]
        found = -1
        for index, networkConfig in enumerate(
                networkConfigSection.get_NetworkConfig()):
            if networkConfig.get_networkName() == network_name:
                found = index
        if found != -1:
            networkConfigSection.NetworkConfig.pop(found)
            output = StringIO()
            networkConfigSection.export(
                output,
                0,
                name_='NetworkConfigSection',
                namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                pretty_print=True)
            body = output.getvalue(). replace(
                "vmw:",
                "").replace(
                'Info xmlns:vmw="http://www.vmware.com/vcloud/v1.5" msgid=""',
                "ovf:Info"). replace(
                "/Info",
                "/ovf:Info")
            self.response = Http.put(
                link.get_href(),
                data=body,
                headers=self.headers,
                verify=self.verify,
                logger=self.logger)
            if self.response.status_code == requests.codes.accepted:
                return taskType.parseString(self.response.content, True)


    def attach_disk_to_vm(self, vm_name, disk_ref, bus_number=None, unit_number=None):
        """
        Attach an independant disk volume to a VM.

        The volume must have been previously added to the VDC.

        :param vm_name: (str): The name of the vm that the disk will be attached to.
        :param disk_ref: (str): The url of a disk resource.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.

        *Note:* A list of disk references for the vdc can be obtained using the VCA get_diskRefs() method
        """
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                body = """
                 <DiskAttachOrDetachParams xmlns="http://www.vmware.com/vcloud/v1.5">
                     <Disk type="application/vnd.vmware.vcloud.disk+xml"
                         href="%s" />
                """ % disk_ref.href
                if bus_number is not None and unit_number is not None:
                    body += """
                          <BusNumber>%s</BusNumber>
                          <UnitNumber>%s</UnitNumber>
                    """ % (bus_number, unit_number)
                body += """
                </DiskAttachOrDetachParams>
                """
                return self.execute("disk:attach", "post", body=body, targetVM=vms[0])


    def detach_disk_from_vm(self, vm_name, disk_ref):
        """
        Detach a disk volume from a VM.

        The volume must have been previously attached to the VM.

        :param vm_name: (str): The name of the vm that the disk will be attached to.
        :param disk_ref: (str): The url of a disk resource.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.

        *Note:* A list of disk references for the vdc can be obtained using the VCA get_diskRefs() method
        """
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                body = """
                 <DiskAttachOrDetachParams xmlns="http://www.vmware.com/vcloud/v1.5">
                     <Disk type="application/vnd.vmware.vcloud.disk+xml"
                         href="%s" />
                 </DiskAttachOrDetachParams>
                """ % disk_ref.href
                return self.execute(
                    "disk:detach", "post", body=body, targetVM=vms[0])

    def vm_media(self, vm_name, media, operation):
        """
        Return a list of details for a media device attached to the VM.
        :param vm_name: (str): The name of the vm.
        :param media_name: (str): The name of the attached media.

        :return: (dict) a dictionary containing media details. \n
         Dictionary keys 'name','type','href'
        """
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                body = """
                 <MediaInsertOrEjectParams xmlns="http://www.vmware.com/vcloud/v1.5">
                     <Media
                       type="%s"
                       name="%s"
                       href="%s" />
                 </MediaInsertOrEjectParams>
                """ % (media.get('name'), media.get('id'), media.get('href'))
                return self.execute(
                    "media:%sMedia" %
                    operation,
                    "post",
                    body=body,
                    targetVM=vms[0])

    def customize_guest_os(self, vm_name, customization_script=None,
                           computer_name=None, admin_password=None,
                           reset_password_required=False):
        """
        Associate a customization script with a guest OS and execute the script.
        The VMware tools must be installed in the Guest OS.

        :param vm_name: (str): The name of the vm to be customized.
        :param customization_script: (str, Optional): The path to a file on the local file system containing the customization script.
        :param computer_name: (str, Optional): A new value for the the computer name. A default value for the template is used if a value is not set.
        :param admin_password: (str, Optional): A password value for the admin/root user. A password is autogenerated if a value is not supplied.
        :param reset_password_required: (bool): Force the user to reset the password on first login.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request. \n
                            if the task cannot be created a debug level log message is generated detailing the reason.

        """
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
                customization_section.export(
                    output,
                    0,
                    name_='GuestCustomizationSection',
                    namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                    pretty_print=True)
                body = output.getvalue(). replace(
                    "vmw:",
                    "").replace(
                    'Info xmlns:vmw="http://www.vmware.com/vcloud/v1.5" msgid=""',
                    "ovf:Info"). replace(
                    "/Info",
                    "/ovf:Info")
                headers = self.headers
                headers[
                    'Content-type'] = 'application/vnd.vmware.vcloud.guestcustomizationsection+xml'
                self.response = Http.put(
                    vms[0].get_href() + '/guestCustomizationSection/',
                    data=body,
                    headers=headers,
                    verify=self.verify,
                    logger=self.logger)
                if self.response.status_code == requests.codes.accepted:
                    return taskType.parseString(self.response.content, True)
                else:
                    Log.debug(
                        self.logger, "failed; response status=%d, content=%s" %
                        (self.response.status_code, self.response.text))

    def force_customization(self, vm_name, power_on=True):
        """
        Force the guest OS customization script to be run for a specific vm in the vApp.
        A customization script must have been previously associated with the VM
        using the pyvcloud customize_guest_os method or using the vCD console
        The VMware tools must be installed in the Guest OS.

        :param vm_name: (str): The name of the vm to be customized.
        :param power_on (bool): Wether to power the vm on after customization or not
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request.b\n
                            if the task cannot be created a debug level log message is generated detailing the reason.

        """
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                sections = vms[0].get_Section()
                links = filter(lambda link: link.rel == "deploy", vms[0].Link)
                if len(links) == 1:
                    forceCustomizationValue = 'true'
                    deployVAppParams = vcloudType.DeployVAppParamsType()
                    if power_on:
                        deployVAppParams.set_powerOn('true')
                    else:
                        deployVAppParams.set_powerOn('false')
                    deployVAppParams.set_deploymentLeaseSeconds(0)
                    deployVAppParams.set_forceCustomization('true')
                    body = CommonUtils.convertPythonObjToStr(
                        deployVAppParams,
                        name="DeployVAppParams",
                        namespacedef='xmlns="http://www.vmware.com/vcloud/v1.5"')
                    headers = self.headers
                    headers[
                        'Content-type'] = 'application/vnd.vmware.vcloud.deployVAppParams+xml'
                    self.response = Http.post(
                        links[0].href,
                        data=body,
                        headers=headers,
                        verify=self.verify,
                        logger=self.logger)
                    if self.response.status_code == requests.codes.accepted:
                        return taskType.parseString(
                            self.response.content, True)
                    else:
                        Log.debug(
                            self.logger, "response status=%d, content=%s" %
                            (self.response.status_code, self.response.text))

    def get_vms_network_info(self):
        """
        List details of the networks associated with each of the vms in the vApp

        :return: (list) a list, one entry per vm, each vm entry contains a list, one entry per network, \n
         each network entry contains a dictionary of properties for the network. \n
         Dictionary keys 'network_name', 'ip', 'mac', 'is_connected', 'is_primary', 'allocation_mode'

        """
        result = []
        vms = self._get_vms()
        for vm in vms:
            nw_connections = []
            sections = vm.get_Section()
            networkConnectionSection = filter(
                lambda section: section.__class__.__name__ == "NetworkConnectionSectionType",
                sections)[0]
            primary_index = networkConnectionSection.get_PrimaryNetworkConnectionIndex()
            connections = networkConnectionSection.get_NetworkConnection()
            for connection in connections:
                nw_connections.append(
                    {'name': vm.name,
                     'network_name': connection.get_network(),
                     'ip': connection.get_IpAddress(),
                     'mac': connection.get_MACAddress(),
                     'is_connected': connection.get_IsConnected(),
                     'is_primary': connection.get_NetworkConnectionIndex() == primary_index,
                     'allocation_mode': connection.get_IpAddressAllocationMode()
                     })
            result.append(nw_connections)
        return result

    def customize_on_next_poweron(self):
        """
        Force the guest OS customization script to be run for the first VM in the vApp.
        A customization script must have been previously associated with the VM
        using the pyvcloud customize_guest_os method or using the vCD console
        The VMware tools must be installed in the Guest OS.

        :return: (bool) True if the request was accepted, False otherwise. If False an error level log message is generated.

        """
        vm = self._get_vms()[0]
        link = filter(lambda link: link.get_rel() == "customizeAtNextPowerOn",
                      vm.get_Link())
        if link:
            self.response = Http.post(link[0].get_href(), data=None,
                                      verify=self.verify, headers=self.headers,
                                      logger=self.logger)
            if self.response.status_code == requests.codes.no_content:
                return True

        Log.error(self.logger, "link not found")
        return False

    def get_vms_details(self):
        """
        Return a list the details for all VMs contained in the vApp.

        :return: (list) a list, one entry per vm containing a (dict) of properties for the VM. \n
         Dictionary keys 'name','status','cpus','memory','memory_mb','os','owner','admin_password','reset_password_required'
        """

        result = []
        children = self.me.get_Children()
        if children:
            vms = children.get_Vm()
            for vm in vms:
                vm_id = vm.get_id()
                name = vm.get_name()
                status = VCLOUD_STATUS_MAP[vm.get_status()]
                owner = self.me.get_Owner().get_User().get_name()
                sections = vm.get_Section()
                env_properties = []
                e = vm.get_Environment()
                if e:
                    es = e.get_Section()
                    property_section = None
                    try:
                        property_section = filter(lambda section: section.__class__.__name__ == 'PropertySection_Type', es)[0]
                    except IndexError:
                        pass
                    if property_section:
                        props = property_section.get_Property()
                        for prop in props:
                            env_properties.append({
                                  prop.anyAttributes_['{http://schemas.dmtf.org/ovf/environment/1}key']:
                                  prop.anyAttributes_['{http://schemas.dmtf.org/ovf/environment/1}value']}
                                  )
                virtualHardwareSection = filter(
                    lambda section: section.__class__.__name__ == "VirtualHardwareSection_Type",
                    sections)[0]
                items = virtualHardwareSection.get_Item()

                cpu = filter(lambda item: item.get_Description().get_valueOf_()
                             == "Number of Virtual CPUs", items)[0]
                cpu_capacity = int(
                    cpu.get_ElementName().get_valueOf_().split(" virtual CPU(s)")[0])

                memory = filter(lambda item: item.get_Description(
                ).get_valueOf_() == "Memory Size", items)[0]
                memory_capacity_mb = int(
                    memory.get_ElementName().get_valueOf_().split(" MB of memory")[0])
                memory_capacity = memory_capacity_mb / 1024

                operatingSystemSection = filter(
                    lambda section: section.__class__.__name__ == "OperatingSystemSection_Type",
                    sections)[0]
                os = operatingSystemSection.get_Description().get_valueOf_()

                customization_section = filter(
                    lambda section: section.__class__.__name__ == "GuestCustomizationSectionType",
                    sections)[0]

                hdd = filter(lambda item: item.get_Description().get_valueOf_() == "Hard disk", items)
                hdd_capacity_mb = 0
                for hdd_item in hdd:
                    hdd_capacity_mb += int(hdd_item.get_HostResource()[0].get_anyAttributes_().get('{http://www.vmware.com/vcloud/v1.5}capacity'))

                result.append(
                    {'id': vm_id,
                     'name': name,
                     'status': status,
                     'cpus': cpu_capacity,
                     'memory': memory_capacity,
                     'memory_mb': memory_capacity_mb,
                     'hdd_mb': hdd_capacity_mb,
                     'os': os,
                     'owner': owner,
                     'admin_password': customization_section.get_AdminPassword(),
                     'reset_password_required': customization_section.get_ResetPasswordRequired(),
                     'env_properties': env_properties
                     }
                )
        Log.debug(self.logger, "details of VMs: %s" % result)
        return result

    def modify_vm_name(self, vm_index, vm_name):
        """
        Modify the name of a VM in a vApp

        :param vm_index: (int):The index of the VM in the vApp 1==first VM
        :param vm_name: (str): The new name of the VM.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request. \n
                            if the task cannot be created a debug level log message is generated detailing the reason.

        :raises: Exception: If the named VM cannot be located or another error occured.
        """
        children = self.me.get_Children()
        if children:
            assert len(children.get_Vm()) >= vm_index
            vm = children.get_Vm()[vm_index - 1]
            assert vm
            href = vm.get_href()
            vm_name_old = vm.get_name()
            Log.debug(
                self.logger, "VM name change (%s) %s -> %s" %
                (vm_index, vm_name_old, vm_name))
            vm.set_name(vm_name)
            vm.set_Section([])
            output = StringIO()
            vm.export(
                output,
                0,
                name_='Vm',
                namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmw="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"',
                pretty_print=True)
            body = output.getvalue()
            headers = self.headers
            headers['Content-type'] = 'application/vnd.vmware.vcloud.vm+xml'
            self.response = Http.post(
                href + '/action/reconfigureVm',
                data=body,
                headers=headers,
                verify=self.verify,
                logger=self.logger)
            if self.response.status_code == requests.codes.accepted:
                return taskType.parseString(self.response.content, True)
            else:
                raise Exception(self.response.status_code)
        raise Exception('can\'t find vm')

    def modify_vm_memory(self, vm_name, new_size):
        """
        Modify the virtual Memory allocation for VM.

        :param vm_name: (str): The name of the vm to be customized.
        :param new_size: (int): The new memory allocation in MB.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request. \n
                            if the task cannot be created a debug level log message is generated detailing the reason.

        :raises: Exception: If the named VM cannot be located or another error occured.
        """
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                vm = vms[0]
                sections = vm.get_Section()
                virtualHardwareSection = filter(
                    lambda section: section.__class__.__name__ == "VirtualHardwareSection_Type",
                    sections)[0]
                items = virtualHardwareSection.get_Item()
                memory = filter(lambda item: item.get_Description(
                ).get_valueOf_() == "Memory Size", items)[0]
                href = memory.get_anyAttributes_().get(
                    '{http://www.vmware.com/vcloud/v1.5}href')
                en = memory.get_ElementName()
                en.set_valueOf_('%s MB of memory' % new_size)
                memory.set_ElementName(en)
                vq = memory.get_VirtualQuantity()
                vq.set_valueOf_(new_size)
                memory.set_VirtualQuantity(vq)
                weight = memory.get_Weight()
                weight.set_valueOf_(str(int(new_size) * 10))
                memory.set_Weight(weight)
                memory_string = CommonUtils.convertPythonObjToStr(
                    memory, 'Memory')
                Log.debug(self.logger, "memory: \n%s" % memory_string)
                output = StringIO()
                memory.export(
                    output,
                    0,
                    name_='Item',
                    namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1" xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData"',
                    pretty_print=True)
                body = output.getvalue(). replace(
                    'Info msgid=""', "ovf:Info").replace(
                    "/Info", "/ovf:Info"). replace(
                    "vmw:", "").replace(
                    "class:", "rasd:").replace(
                    "ResourceType", "rasd:ResourceType")
                headers = self.headers
                headers[
                    'Content-type'] = 'application/vnd.vmware.vcloud.rasdItem+xml'
                self.response = Http.put(
                    href,
                    data=body,
                    headers=headers,
                    verify=self.verify,
                    logger=self.logger)
                if self.response.status_code == requests.codes.accepted:
                    return taskType.parseString(self.response.content, True)
                else:
                    raise Exception(self.response.status_code)
        raise Exception('can\'t find vm')

    def modify_vm_cpu(self, vm_name, cpus):
        """
        Modify the virtual CPU allocation for VM.

        :param vm_name: (str): The name of the vm to be customized.
        :param cpus: (int): The number of virtual CPUs allocated to the VM.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request. \n
                            if the task cannot be created a debug level log message is generated detailing the reason.

        :raises: Exception: If the named VM cannot be located or another error occured.
        """
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                vm = vms[0]
                sections = vm.get_Section()
                virtualHardwareSection = filter(
                    lambda section: section.__class__.__name__ == "VirtualHardwareSection_Type",
                    sections)[0]
                items = virtualHardwareSection.get_Item()
                cpu = filter(lambda item: (item.get_anyAttributes_().get('{http://www.vmware.com/vcloud/v1.5}href') is not None and item.get_anyAttributes_(
                ).get('{http://www.vmware.com/vcloud/v1.5}href').endswith('/virtualHardwareSection/cpu')), items)[0]
                href = cpu.get_anyAttributes_().get(
                    '{http://www.vmware.com/vcloud/v1.5}href')
                en = cpu.get_ElementName()
                en.set_valueOf_('%s virtual CPU(s)' % cpus)
                cpu.set_ElementName(en)
                vq = cpu.get_VirtualQuantity()
                vq.set_valueOf_(cpus)
                cpu.set_VirtualQuantity(vq)
                cpu_string = CommonUtils.convertPythonObjToStr(cpu, 'CPU')
                output = StringIO()
                cpu.export(
                    output,
                    0,
                    name_='Item',
                    namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1" xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData"',
                    pretty_print=True)
                body = output.getvalue(). replace(
                    'Info msgid=""', "ovf:Info").replace(
                    "/Info", "/ovf:Info"). replace(
                    "vmw:", "").replace(
                    "class:", "rasd:").replace(
                    "ResourceType", "rasd:ResourceType")
                headers = self.headers
                headers[
                    'Content-type'] = 'application/vnd.vmware.vcloud.rasdItem+xml'
                self.response = Http.put(
                    href,
                    data=body,
                    headers=headers,
                    verify=self.verify,
                    logger=self.logger)
                if self.response.status_code == requests.codes.accepted:
                    return taskType.parseString(self.response.content, True)
                else:
                    raise Exception(self.response.status_code)
        raise Exception('can\'t find vm')

    def add_disk_to_vm(self, vm_name, disk_size, storage_profile_href=None):
        """
        Add a virtual disk to a virtual machine in the vApp.

        :param vm_name: (str): The name of the vm to be customized.
        :param disk_size: (int): The size of the disk to be added, in MBs.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the request. \n
                            if the task cannot be created a debug level log message is generated detailing the reason.

        :raises: Exception: If the named VM cannot be located or another error occured.
        """
        children = self.me.get_Children()
        if children:
            vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
            if len(vms) == 1:
                vm = vms[0]
                href = vm.get_href() + "/virtualHardwareSection/disks"
                headers = self.headers
                self.response = Http.get(href, headers=headers, verify=self.verify, logger=self.logger)
                diskItemsList = None
                if self.response.status_code == requests.codes.ok:
                    diskItemsList = vcloudType.parseString(self.response.content, True)
                else:
                    error = errorType.parseString(self.response.content, True)
                    raise Exception(error.message)

                disks = filter(lambda x: x.get_Description().get_valueOf_() == 'Hard disk',
                               diskItemsList.get_Item())

                if len(disks) > 0:
                    lastDisk = reduce(lambda a, b:
                            a.AddressOnParent.get_valueOf_() if a.AddressOnParent.get_valueOf_() >
                            b.AddressOnParent.get_valueOf_() else b.AddressOnParent.get_valueOf_(),
                        disks)

                    new_disk = copy.deepcopy(lastDisk)
                    new_disk.AddressOnParent.set_valueOf_((int(lastDisk.AddressOnParent.get_valueOf_())
                        + 1))
                    new_disk.InstanceID.set_valueOf_((int(lastDisk.InstanceID.get_valueOf_()) + 1))
                    new_disk.ElementName.set_valueOf_('Hard disk ' +
                            str(int(lastDisk.AddressOnParent.get_valueOf_()) + 2))
                    new_disk.VirtualQuantity.set_valueOf_(disk_size * 1024 * 1024)
                    ns = '{http://www.vmware.com/vcloud/v1.5}'
                    for hr in new_disk.HostResource:
                        attributes = hr.get_anyAttributes_()
                        attributes.update({ns + 'capacity': disk_size})
                        if storage_profile_href is not None:
                            sp = {
                                ns + 'storageProfileOverrideVmDefault': True,
                                ns + 'storageProfileHref': storage_profile_href,
                            }
                            attributes.update(sp)

                        hr.set_anyAttributes_(attributes)
                    diskItemsList.add_Item(new_disk)

                output = StringIO()
                diskItemsList.export(
                    output,
                    0,
                    name_='RasdItemsList',
                    namespacedef_='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1" xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
                    pretty_print=True)
                body = output.getvalue(). replace(
                    'Info msgid=""', "ovf:Info").replace(
                    "/Info", "/ovf:Info"). replace(
                    "vmw:", "").replace(
                    "class:", "rasd:").replace(
                    "ResourceType", "rasd:ResourceType")
                headers = self.headers
                headers['Content-type'] = 'application/vnd.vmware.vcloud.rasditemslist+xml'

                self.response = Http.put(
                    href,
                    data=body,
                    headers=headers,
                    verify=self.verify,
                    logger=self.logger)
                if self.response.status_code == requests.codes.accepted:
                    return taskType.parseString(self.response.content, True)
                else:
                    error = errorType.parseString(self.response.content, True)
                    raise Exception(error.message)
        raise Exception('can\'t find vm')

    def _get_vms(self):
        children = self.me.get_Children()
        if children:
            return children.get_Vm()
        else:
            return []

    def _modify_networkConnectionSection(self, section, new_connection,
                                         primary_index=None):

        # Need to add same interface more than once for a VM , so commenting
        # out below lines

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

    def _create_networkConnection(
            self,
            network_name,
            index,
            ip_allocation_mode,
            mac_address=None,
            ip_address=None):
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
