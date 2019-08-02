# VMware vCloud Director Python SDK
# Copyright (c) 2014-2019 VMware, Inc. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.vapp_services import VappServices


class VappNat(VappServices):
    def _makeNatServiceAttr(features):
        nat_service = E.NatService()
        nat_service.append(E.IsEnabled(True))
        nat_service.append(E.NatType('ipTranslation'))
        nat_service.append(E.Policy('allowTrafficIn'))
        features.append(nat_service)

    def _delete_all_nat_rule(nat_service):
        if hasattr(nat_service, 'NatRule'):
            for nat_rule in nat_service.NatRule:
                nat_service.remove(nat_rule)

    def enable_nat_service(self, isEnable):
        """Enable NAT service to vApp network.

        :param bool isEnable: True for enable and False for Disable.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable NAT service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable NAT service failed as given network's connection "
                "is not routed")
        features = self.resource.Configuration.Features
        if not hasattr(features, 'NatService'):
            VappNat._makeNatServiceAttr(features)
        nat_service = features.NatService
        nat_service.IsEnabled = E.IsEnabled(isEnable)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.vApp_Network.value,
                                               self.resource)

    def update_nat_type(self,
                        nat_type='ipTranslation',
                        policy='allowTrafficIn'):
        """Update NAT type to vApp network.

        :param str nat_type: NAT type (portForwarding/ipTranslation).
        :param str policy: policy type(allowTrafficIn/allowTraffic).
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable NAT service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable NAT service failed as given network's connection "
                "is not routed")
        features = self.resource.Configuration.Features
        if not hasattr(features, 'NatService'):
            VappNat._makeNatServiceAttr(features)
        nat_service = features.NatService
        if nat_service.NatType != nat_type:
            VappNat._delete_all_nat_rule(nat_service)
        nat_service.NatType = E.NatType(nat_type)
        nat_service.Policy = E.Policy(policy)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.vApp_Network.value,
                                               self.resource)

    def add_nat_rule(self,
                     nat_type,
                     vapp_scoped_vm_id,
                     vm_nic_id,
                     mapping_mode='automatic',
                     external_ip_address=None,
                     external_port=-1,
                     internal_port=-1,
                     protocol='TCP'):
        """Add NAT rule to vApp network.

        :param str nat_type: NAT type (portForwarding/ipTranslation).
        :param str vapp_scoped_vm_id: vapp network scoped vm id.
        :param str vm_nic_id: vapp network scoped vm nic id.
        :param str mapping_mode: NAT rule mapping mode (automatic/manual) if
            nat_type is ipTranslation.
        :param str external_ip_address: external ip address if mapping mode is
            manual.
        :param int external_port: external port of NAT rule if nat_type is
            portForwarding.
        :param int internal_port: internal port of NAT rule if nat_type is
            portForwarding.
        :param str protocol: protocol of NAT rule if nat_type is
            portForwarding.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable NAT service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable NAT service failed as given network's connection "
                "is not routed")
        features = self.resource.Configuration.Features
        if not hasattr(features, 'NatService'):
            VappNat._makeNatServiceAttr(features)
        nat_service = features.NatService
        if nat_service.NatType != nat_type:
            VappNat._delete_all_nat_rule(nat_service)
            nat_service.NatType = E.NatType(nat_type)
        nat_rule = E.NatRule()
        if nat_type == 'ipTranslation':
            one_to_vm_rule = E.OneToOneVmRule()
            one_to_vm_rule.append(E.MappingMode(mapping_mode))
            if mapping_mode == 'manual':
                one_to_vm_rule.append(E.ExternalIpAddress(external_ip_address))
            one_to_vm_rule.append(E.VAppScopedVmId(vapp_scoped_vm_id))
            one_to_vm_rule.append(E.VmNicId(vm_nic_id))
            nat_rule.append(one_to_vm_rule)
        elif nat_type == 'portForwarding':
            vm_rule = E.VmRule()
            vm_rule.append(E.ExternalPort(external_port))
            vm_rule.append(E.VAppScopedVmId(vapp_scoped_vm_id))
            vm_rule.append(E.VmNicId(vm_nic_id))
            vm_rule.append(E.InternalPort(internal_port))
            vm_rule.append(E.Protocol(protocol))
            nat_rule.append(vm_rule)
        nat_service.append(nat_rule)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.vApp_Network.value,
                                               self.resource)
