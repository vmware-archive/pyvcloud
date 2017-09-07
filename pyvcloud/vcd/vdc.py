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

from lxml import objectify
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.org import Org


Maker = objectify.ElementMaker(
    annotate=False,
    namespace='',
    nsmap={None: 'http://www.vmware.com/vcloud/v1.5'})


OvfMaker = objectify.ElementMaker(
    annotate=False,
    namespace='http://schemas.dmtf.org/ovf/envelope/1',
    nsmap={None: 'http://schemas.dmtf.org/ovf/envelope/1'})


class VDC(object):

    def __init__(self, client, name=None, vdc_href=None, vdc_resource=None):
        self.client = client
        self.name = name
        self.href = vdc_href
        self.vdc_resource = vdc_resource
        if vdc_resource is not None:
            self.name = vdc_resource.get('name')
            self.href = vdc_resource.get('href')

    def get_resource(self):
        if self.vdc_resource is None:
            self.vdc_resource = self.client.get_resource(self.href)
        return self.vdc_resource

    def get_resource_href(self, name, entity_type=EntityType.VAPP):
        if self.vdc_resource is None:
            self.vdc_resource = self.client.get_resource(self.href)
        result = []
        if hasattr(self.vdc_resource, 'ResourceEntities') and \
           hasattr(self.vdc_resource.ResourceEntities, 'ResourceEntity'):
            for vapp in self.vdc_resource.ResourceEntities.ResourceEntity:
                if vapp.get('name') == name:
                    result.append(vapp.get('href'))
        if len(result) == 0:
            raise Exception('not found')
        elif len(result) > 1:
            raise Exception('more than one found, use the vapp-id')
        return result[0]

    def get_vapp(self, name):
        return self.client.get_resource(self.get_resource_href(name))

    def delete_vapp(self, name, force=False):
        href = self.get_resource_href(name)
        return self.client.delete_resource(href, force)

    def instantiate_vapp(self,
                         name,
                         catalog,
                         template,
                         network=None,
                         fence_mode='bridged',
                         deploy=True,
                         power_on=True,
                         accept_all_eulas=True):
        if self.vdc_resource is None:
            self.vdc_resource = self.client.get_resource(self.href)

        network_href = None
        if hasattr(self.vdc_resource, 'AvailableNetworks') and \
           hasattr(self.vdc_resource.AvailableNetworks, 'Network'):
            for n in self.vdc_resource.AvailableNetworks.Network:
                if network is None or n.get('name') == network:
                    network_href = n.get('href')
        if network_href is None:
            raise Exception('Network not found in the Virtual Datacenter.')

        # TODO(cache some of these objects here and in Org object)
        org_href = find_link(self.vdc_resource,
                             RelationType.UP,
                             EntityType.ORG.value).href
        org = Org(self.client, org_href)
        template_resource = org.get_catalog_item(catalog, template)
        v = self.client.get_resource(template_resource.Entity.get('href'))
        n = v.xpath(
            '//ovf:NetworkSection/ovf:Network',
            namespaces={'ovf': 'http://schemas.dmtf.org/ovf/envelope/1'})
        network_name = n[0].get('{http://schemas.dmtf.org/ovf/envelope/1}name')
        vm_id = v.Children[0].Vm.VAppScopedLocalId.text
        deploy_param = 'true' if deploy else 'false'
        power_on_param = 'true' if power_on else 'false'
        network_configuration = Maker.Configuration(
            Maker.ParentNetwork(href=network_href),
            Maker.FenceMode(fence_mode)
        )
        if fence_mode == 'natRouted':
            # network_name = network
            network_configuration.append(
                Maker.Features(
                    Maker.NatService(
                        Maker.IsEnabled('true'),
                        Maker.NatType('ipTranslation'),
                        Maker.Policy('allowTraffic'),
                        Maker.NatRule(
                            Maker.OneToOneVmRule(
                                Maker.MappingMode('automatic'),
                                Maker.VAppScopedVmId(vm_id),
                                Maker.VmNicId(0)
                            )
                        )
                    )
                )
            )
        vapp_template_params = Maker.InstantiateVAppTemplateParams(
            name=name,
            deploy=deploy_param,
            powerOn=power_on_param)
        vapp_template_params.append(
            Maker.InstantiationParams(
                Maker.NetworkConfigSection(
                    OvfMaker.Info('Configuration for logical networks'),
                    Maker.NetworkConfig(
                        network_configuration,
                        networkName=network_name
                    )
                )
            )
        )
        vapp_template_params.append(
            Maker.Source(href=template_resource.Entity.get('href'))
        )
        vm = v.xpath(
            '//vcloud:VAppTemplate/vcloud:Children/vcloud:Vm',
            namespaces=NSMAP)
        # for c in vm[0].NetworkConnectionSection.NetworkConnection:
        #     c.remove(c.MACAddress)
        #     # c.remove(c.IpAddressAllocationMode)
        #     # tmp = c.NetworkAdapterType
        #     # c.remove(c.NetworkAdapterType)
        #     # c.append(Maker.IpAddressAllocationMode('POOL'))
        #     # c.append(tmp)
        ip = Maker.InstantiationParams()
        # ip.append(vm[0].NetworkConnectionSection)
        gc = Maker.GuestCustomizationSection(
            OvfMaker.Info('Specifies Guest OS Customization Settings'),
            Maker.Enabled('false'),
            # Maker.AdminPasswordEnabled('false'),
            Maker.ComputerName(name)
        )
        ip.append(gc)
        all_eulas_accepted = 'true' if accept_all_eulas else 'false'
        vapp_template_params.append(
            Maker.SourcedItem(
                Maker.Source(href=vm[0].get('href'),
                             id=vm[0].get('id'),
                             name=vm[0].get('name'),
                             type=vm[0].get('type')),
                Maker.VmGeneralParams(
                    Maker.Name(name),
                    Maker.NeedsCustomization('false')
                ),
                ip
            )
        )
        vapp_template_params.append(Maker.AllEULAsAccepted(all_eulas_accepted))
        return self.client.post_resource(
            self.href+'/action/instantiateVAppTemplate',
            vapp_template_params,
            EntityType.INSTANTIATE_VAPP_TEMPLATE_PARAMS.value)

    # def reconfigure_vapp_network(self,
    #                      name,
    #                      network=None,
    #                      fence_mode='bridged'):
    #     if self.vdc_resource is None:
    #         self.vdc_resource = self.client.get_resource(self.href)
    #
    #     org_vdc_network_name = None
    #     network_href = None
    #     if hasattr(self.vdc_resource, 'AvailableNetworks') and \
    #        hasattr(self.vdc_resource.AvailableNetworks, 'Network'):
    #         for n in self.vdc_resource.AvailableNetworks.Network:
    #             if network is None or n.get('name') == network:
    #                 network_href = n.get('href')
    #                 org_vdc_network_name = n.get('name')
    #     if network_href is None:
    #         raise Exception('Network not found in the Virtual Datacenter.')
    #
    #     v = self.get_vapp(name)
    #     from lxml import etree
    #     print()
    #     print(etree.tounicode(v.NetworkConfigSection, pretty_print=True))
    #     href = v.NetworkConfigSection.get('href')
    #     print(href)
    #     v.NetworkConfigSection.NetworkConfig.Configuration.FenceMode =
    #           Maker.FenceMode('natRouted')
    #     print(etree.tounicode(v.NetworkConfigSection, pretty_print=True))
    #     return self.client.put_resource(
    #         href,
    #         v.NetworkConfigSection,
    #         EntityType.NETWORK_CONFIG_SECTION.value)

    def list_resources(self, entity_type=None):
        if self.vdc_resource is None:
            self.vdc_resource = self.client.get_resource(self.href)
        result = []
        if hasattr(self.vdc_resource, 'ResourceEntities') and \
           hasattr(self.vdc_resource.ResourceEntities, 'ResourceEntity'):
            for vapp in self.vdc_resource.ResourceEntities.ResourceEntity:
                if entity_type is None or \
                   entity_type.value == vapp.get('type'):
                    result.append({'name': vapp.get('name')})
        return result
