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
from pyvcloud.vcd.exceptions import EntityNotFoundException
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

    def get_nat_type(self):
        """Get NAT type to vApp network.

        :return: dictionary contain nat type and policy.
        :rtype: dict
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
        nat_detail = {}
        nat_detail['NatType'] = nat_service.NatType
        nat_detail['Policy'] = nat_service.Policy
        return nat_detail

    def get_list_of_nat_rule(self):
        """List NAT rules of vApp network.

        :return: list of dictionary contain detail of NAT rule.
        :rtype: list
        :raises: InvalidParameterException: Enable NAT service failed as
            given network's connection is not routed
        """
        list_of_nat_rules = []
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            return list_of_nat_rules
        features = self.resource.Configuration.Features
        if not hasattr(features, 'NatService'):
            return list_of_nat_rules
        nat_service = features.NatService
        if hasattr(nat_service, 'NatRule'):
            if nat_service.NatType == 'ipTranslation':
                list_of_nat_rules = VappNat._get_ip_translation_nat_rule(
                    nat_service)
            elif nat_service.NatType == 'portForwarding':
                list_of_nat_rules = VappNat._get_port_forwarding_nat_rule(
                    nat_service)
        return list_of_nat_rules

    def _get_ip_translation_nat_rule(nat_service):
        """Get list of IP translation NAT rules of vApp network.

        :return: list of dictionary contain detail of NAT rule.
        :rtype: list
        """
        list_of_nat_rules = []
        for nat_rule in nat_service.NatRule:
            rule_detail = {}
            rule_detail['Id'] = nat_rule.Id
            if hasattr(nat_rule, 'OneToOneVmRule'):
                one_to_one_rule = nat_rule.OneToOneVmRule
                rule_detail['MappingMode'] = one_to_one_rule.MappingMode
                rule_detail['VAppScopedVmId'] = one_to_one_rule.VAppScopedVmId
                rule_detail['VmNicId'] = one_to_one_rule.VmNicId
                if hasattr(one_to_one_rule, 'ExternalIpAddress'):
                    rule_detail['ExternalIpAddress'] = \
                        one_to_one_rule.ExternalIpAddress
            list_of_nat_rules.append(rule_detail)
        return list_of_nat_rules

    def _get_port_forwarding_nat_rule(nat_service):
        """Get list of port forwarding NAT rules of vApp network.

        :return: list of dictionary contain detail of NAT rule.
        :rtype: list
        """
        list_of_nat_rules = []
        for nat_rule in nat_service.NatRule:
            rule_detail = {}
            rule_detail['Id'] = nat_rule.Id
            if hasattr(nat_rule, 'VmRule'):
                vm_rule = nat_rule.VmRule
                rule_detail['VAppScopedVmId'] = vm_rule.VAppScopedVmId
                rule_detail['VmNicId'] = vm_rule.VmNicId
                rule_detail['ExternalPort'] = vm_rule.ExternalPort
                rule_detail['InternalPort'] = vm_rule.InternalPort
                rule_detail['Protocol'] = vm_rule.Protocol
            list_of_nat_rules.append(rule_detail)
        return list_of_nat_rules

    def delete_nat_rule(self, id):
        """Delete NAT rules from vApp network.

        :param str id: id of NAT rule.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable NAT service failed as
            given network's connection is not routed
        :raises: EntityNotFoundException: if the NAT rule not exist of give id.
        """
        list_of_nat_rules = []
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable NAT service failed as given network's connection "
                "is not routed")
        features = self.resource.Configuration.Features
        if not hasattr(features, 'NatService'):
            return list_of_nat_rules
        nat_service = features.NatService
        is_deleted = False
        for nat_rule in nat_service.NatRule:
            if nat_rule.Id == int(id):
                nat_service.remove(nat_rule)
                is_deleted = True
        if not is_deleted:
            raise EntityNotFoundException('NAT rule ' + id +
                                          ' doesn\'t exist.')
        else:
            return self.client.put_linked_resource(
                self.resource, RelationType.EDIT,
                EntityType.vApp_Network.value, self.resource)

    def update_nat_rule(self,
                        rule_id,
                        vapp_scoped_vm_id=None,
                        vm_nic_id=None,
                        mapping_mode=None,
                        external_ip_address=None,
                        external_port=None,
                        internal_port=None,
                        protocol=None):
        """Update NAT rule of vApp network.

        :param str rule_id: id of NAT rule.
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
        :raises: EntityNotFoundException: if the NAT rule not exist of give id.
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable NAT service failed as given network's connection "
                "is not routed")
        if not hasattr(self.resource.Configuration.Features, 'NatService'):
            raise EntityNotFoundException('NAT rule ' + id +
                                          ' doesn\'t exist.')
        nat_service = self.resource.Configuration.Features.NatService
        is_updated = False
        for nat_rule in nat_service.NatRule:
            if nat_rule.Id == int(rule_id):
                if nat_service.NatType == 'ipTranslation':
                    VappNat._update_ip_translation_nat_rule(
                        nat_rule=nat_rule,
                        vapp_scoped_vm_id=vapp_scoped_vm_id,
                        vm_nic_id=vm_nic_id,
                        mapping_mode=mapping_mode,
                        ext_ip_address=external_ip_address)
                elif nat_service.NatType == 'portForwarding':
                    VappNat._update_port_forwarding_nat_rule(
                        nat_rule=nat_rule,
                        vapp_scoped_vm_id=vapp_scoped_vm_id,
                        vm_nic_id=vm_nic_id,
                        external_port=external_port,
                        internal_port=internal_port,
                        protocol=protocol)
                is_updated = True
        if not is_updated:
            raise EntityNotFoundException('NAT rule ' + id +
                                          ' doesn\'t exist.')
        else:
            return self.client.put_linked_resource(
                self.resource, RelationType.EDIT,
                EntityType.vApp_Network.value, self.resource)

    def _update_ip_translation_nat_rule(nat_rule,
                                        vapp_scoped_vm_id=None,
                                        vm_nic_id=None,
                                        mapping_mode=None,
                                        ext_ip_address=None):
        """Update IP translation NAT rule of vApp network.

        :param str vapp_scoped_vm_id: vapp network scoped vm id.
        :param str vm_nic_id: vapp network scoped vm nic id.
        :param str mapping_mode: NAT rule mapping mode (automatic/manual) if
            nat_type is ipTranslation.
        :param str external_ip_address: external ip address if mapping mode is
            manual.
        """
        one_to_one_rule = nat_rule.OneToOneVmRule
        if vapp_scoped_vm_id is not None:
            one_to_one_rule.VAppScopedVmId = E.VAppScopedVmId(
                vapp_scoped_vm_id)
        if vm_nic_id is not None:
            one_to_one_rule.VmNicId = E.VmNicId(vm_nic_id)
        if mapping_mode is not None:
            one_to_one_rule.MappingMode = E.MappingMode(mapping_mode)
        if ext_ip_address is not None:
            ext_ip_node = E.ExternalIpAddress(ext_ip_address)
            if one_to_one_rule.MappingMode == 'manual' and hasattr(
                    one_to_one_rule, 'ExternalIpAddress'):
                one_to_one_rule.ExternalIpAddress = ext_ip_node
            elif one_to_one_rule.MappingMode == 'manual':
                one_to_one_rule.MappingMode.addnext(ext_ip_node)

    def _update_port_forwarding_nat_rule(nat_rule,
                                         vapp_scoped_vm_id=None,
                                         vm_nic_id=None,
                                         external_port=None,
                                         internal_port=None,
                                         protocol=None):
        """Update port forwarding NAT rule of vApp network.

        :param str vapp_scoped_vm_id: vapp network scoped vm id.
        :param str vm_nic_id: vapp network scoped vm nic id.
        :param int external_port: external port of NAT rule if nat_type is
            portForwarding.
        :param int internal_port: internal port of NAT rule if nat_type is
            portForwarding.
        :param str protocol: protocol of NAT rule if nat_type.
        """
        vm_rule = nat_rule.VmRule
        if vapp_scoped_vm_id is not None:
            vm_rule.VAppScopedVmId = E.VAppScopedVmId(vapp_scoped_vm_id)
        if vm_nic_id is not None:
            vm_rule.VmNicId = E.VmNicId(vm_nic_id)
        if external_port is not None:
            vm_rule.ExternalPort = E.ExternalPort(external_port)
        if internal_port is not None:
            vm_rule.InternalPort = E.InternalPort(internal_port)
        if protocol is not None:
            vm_rule.Protocol = E.Protocol(protocol)
