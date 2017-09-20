# vCloud Air CLI 0.1
#
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
#
# This product is licensed to you under the
# Apache License, Version 2.0 (the "License").
# You may not use this product except in compliance with the License.
#
# This product may include a number of subcomponents with
# separate copyright notices and license terms. Your use of the source
# code for the these subcomponents is subject to the terms and
# conditions of the subcomponent's license, as noted in the LICENSE file.
#


from configparser import ConfigParser
from cryptography.fernet import Fernet
import operator
import os
from pyvcloud import _get_logger
from pyvcloud import Log
from pyvcloud.vcloudair import VCA
from pyvcloud.vcloudsession import VCS
import traceback
from vca_cli_utils import VcaCliUtils


utils = VcaCliUtils()


class CmdProc(object):
    crypto_key = 'l1ZLY5hYPu4s2IXkTVxtndJ-L_k16rP1odagwhP_DsY='
    DISK_SIZE = 1000000000

    def __init__(self, profile=None, profile_file=None,
                 json_output=False, xml_output=False,
                 debug=False, insecure=None):
        self.profile = profile
        self.profile_file = profile_file
        self.debug = debug
        self.json_output = json_output
        self.xml_output = xml_output
        self.password = None
        self.config = ConfigParser.RawConfigParser()
        self.vca = None
        self.instance = None
        self.logger = _get_logger() if debug else None
        self.error_message = None
        self.vdc_name = None
        self.gateway = None
        self.insecure = insecure
        self.verify = True

    def load_config(self, profile=None, profile_file='~/.vcarc'):
        self.config.read(os.path.expanduser(profile_file))
        if profile is not None:
            self.profile = profile
        else:
            section = 'Global'
            if self.config.has_option(section, 'profile'):
                self.profile = self.config.get(section, 'profile')
            else:
                self.profile = 'default'
        host = 'vca.vmware.com'
        user = None
        password = None
        token = None
        service_type = None
        version = None
        section = 'Profile-%s' % self.profile
        instance = None
        org = None
        org_url = None
        session_token = None
        session_uri = None
        vdc = None
        gateway = None
        verify = True
        if self.config.has_section(section):
            if self.config.has_option(section, 'host'):
                host = self.config.get(section, 'host')
            if self.insecure is not None:
                verify = not self.insecure
            else:
                if self.config.has_option(section, 'verify'):
                    verify = self.config.get(section, 'verify') == 'True'
            if self.config.has_option(section, 'user'):
                user = self.config.get(section, 'user')
            if self.config.has_option(section, 'password'):
                password = self.config.get(section, 'password')
                if len(password) > 0:
                    cipher_suite = Fernet(self.crypto_key)
                    password = cipher_suite.decrypt(password)
            if self.config.has_option(section, 'token'):
                token = self.config.get(section, 'token')
            if self.config.has_option(section, 'service_type'):
                service_type = self.config.get(section, 'service_type')
            if self.config.has_option(section, 'service_version'):
                version = self.config.get(section, 'service_version')
            if self.config.has_option(section, 'instance'):
                instance = self.config.get(section, 'instance')
            if self.config.has_option(section, 'org'):
                org = self.config.get(section, 'org')
            if self.config.has_option(section, 'org_url'):
                org_url = self.config.get(section, 'org_url')
            if self.config.has_option(section, 'session_token'):
                session_token = self.config.get(section, 'session_token')
            if self.config.has_option(section, 'session_uri'):
                session_uri = self.config.get(section, 'session_uri')
            if self.config.has_option(section, 'vdc'):
                vdc = self.config.get(section, 'vdc')
            if self.config.has_option(section, 'gateway'):
                gateway = self.config.get(section, 'gateway')
        self.verify = verify
        self.vca = VCA(host=host, username=user,
                       service_type=service_type, version=version,
                       verify=self.verify, log=self.debug)
        self.password = password
        self.vca.token = token
        self.vca.org = org
        self.instance = instance
        if session_token is not None:
            vcloud_session = VCS(url=session_uri,
                                 username=user,
                                 org=org,
                                 instance=instance,
                                 api_url=org_url,
                                 org_url=org_url,
                                 version=version,
                                 verify=self.verify,
                                 log=self.debug)
            vcloud_session.token = session_token
            self.vca.vcloud_session = vcloud_session
            self.vdc_name = vdc
            self.gateway = gateway
        Log.debug(self.logger, 'restored vca %s' % self.vca)
        if self.vca.vcloud_session is not None:
            Log.debug(self.logger, 'restored vcloud_session %s' %
                      self.vca.vcloud_session)
            Log.debug(self.logger, 'restored org=%s' % self.vca.org)
            if self.vca.vcloud_session.token is not None:
                Log.debug(self.logger, 'restored vcloud_session token %s' %
                          self.vca.vcloud_session.token)

    def print_profile_file(self):
        headers = ['Profile', 'Selected', 'Host', 'Verify', 'Type', 'User',
                   'Instance', 'Org', 'vdc']
        table = []
        for section in self.config.sections():
            if section.startswith('Profile-'):
                section_name = section.split('-')[1]
                selected = '*' if section_name == self.profile else ''
                host = self.config.get(section, 'host') \
                    if self.config.has_option(section, 'host') else ''
                insecure = self.config.get(section, 'verify') \
                    if self.config.has_option(section, 'verify') else ''
                service_type = self.config.get(section, 'service_type') \
                    if self.config.has_option(section, 'service_type') else ''
                user = self.config.get(section, 'user') \
                    if self.config.has_option(section, 'user') else ''
                instance = self.config.get(section, 'instance') \
                    if self.config.has_option(section, 'instance') else ''
                org = self.config.get(section, 'org') \
                    if self.config.has_option(section, 'org') else ''
                vdc = self.config.get(section, 'vdc') \
                    if self.config.has_option(section, 'vdc') else ''
                table.append([section_name,
                              selected,
                              host,
                              insecure,
                              service_type,
                              user,
                              instance,
                              org,
                              vdc])
        utils.print_table('Profiles in file %s:' %
                          self.profile_file, headers, table, self)

    def save_current_config(self):
        self.save_config(self.profile, self.profile_file)

    def save_config(self, profile='default', profile_file='~/.vcarc'):
        section = 'Global'
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, 'profile', profile)
        section = 'Profile-%s' % profile
        if not self.config.has_section(section):
            self.config.add_section(section)
        if self.vca is None or self.vca.host is None:
            self.config.remove_option(section, 'host')
        else:
            self.config.set(section, 'host', self.vca.host)
        if self.vca is None or self.vca.username is None:
            self.config.remove_option(section, 'user')
        else:
            self.config.set(section, 'user', self.vca.username)
        if self.vca is None or self.vca.service_type is None:
            self.config.remove_option(section, 'service_type')
        else:
            self.config.set(section, 'service_type', self.vca.service_type)
        if self.vca is None or self.vca.version is None:
            self.config.remove_option(section, 'service_version')
        else:
            self.config.set(section, 'service_version', self.vca.version)
        if self.vca is None or self.vca.token is None:
            self.config.remove_option(section, 'token')
        else:
            self.config.set(section, 'token', self.vca.token)
        if self.password is not None and len(self.password) > 0:
            cipher_suite = Fernet(self.crypto_key)
            cipher_text = cipher_suite.encrypt(self.password.encode('utf-8'))
            self.config.set(section, 'password', cipher_text)
        else:
            self.config.remove_option(section, 'password')
        if self.instance is None:
            self.config.remove_option(section, 'instance')
        else:
            self.config.set(section, 'instance', self.instance)
        if self.vca is None or self.vca.vcloud_session is None:
            self.config.remove_option(section, 'org')
            self.config.remove_option(section, 'org_url')
            self.config.remove_option(section, 'session_token')
            self.config.remove_option(section, 'session_uri')
            self.config.remove_option(section, 'vdc')
            self.config.remove_option(section, 'gateway')
        else:
            if self.vca.org is None:
                self.config.remove_option(section, 'org')
            else:
                self.config.set(section, 'org', self.vca.org)
            if self.vca.vcloud_session.url is None:
                self.config.remove_option(section, 'session_uri')
            else:
                self.config.set(section, 'session_uri',
                                self.vca.vcloud_session.url)
            if self.vca.vcloud_session.org_url is None:
                self.config.remove_option(section, 'org_url')
            else:
                self.config.set(section, 'org_url',
                                self.vca.vcloud_session.org_url)
            if self.vca.vcloud_session.token is None:
                self.config.remove_option(section, 'session_token')
            else:
                self.config.set(section, 'session_token',
                                self.vca.vcloud_session.token)
            if self.vdc_name is None:
                self.config.remove_option(section, 'vdc')
            else:
                self.config.set(section, 'vdc', self.vdc_name)
            if self.gateway is None:
                self.config.remove_option(section, 'gateway')
            else:
                self.config.set(section, 'gateway', self.gateway)
        self.config.set(section, 'verify', self.verify)
        with open(os.path.expanduser(profile_file), 'w+') as configfile:
            self.config.write(configfile)

    def login(self, host, username, password, instance, org, version,
              save_password=True):
        self.vca = VCA(host=host, username=username, version=version,
                       verify=self.verify, log=self.debug)
        service_type = self.vca.get_service_type()
        if service_type == VCA.VCA_SERVICE_TYPE_UNKNOWN:
            raise Exception('service type unknown')
        self.vca.service_type = service_type
        if VCA.VCA_SERVICE_TYPE_STANDALONE == service_type and \
           org is None:
            self.error_message = 'Org can\'t be null'
            return False
        result = self.vca.login(password=password, org=org)
        if result:
            Log.debug(self.logger, 'logged in, org=%s' % self.vca.org)
            if VCA.VCA_SERVICE_TYPE_STANDALONE == service_type:
                result = self.vca.vcloud_session.login(token=self.vca.
                                                       vcloud_session.token)
                assert result
            if save_password:
                self.password = password
            self.save_config(self.profile, self.profile_file)
        return result

    def re_login_vcloud_session(self):
        Log.debug(self.logger, 'about to re-login vcloud_session vca=%s' %
                  self.vca)
        if self.vca.vcloud_session is not None:
            Log.debug(self.logger, 'about to re-login vcloud_session=%s' %
                      self.vca.vcloud_session)
            if self.vca.vcloud_session.token is not None:
                Log.debug(self.logger,
                          'about to re-login vcloud_session token=%s' %
                          self.vca.vcloud_session.token)
        if self.vca.vcloud_session is not None and \
           self.vca.vcloud_session.token is not None:
            result = self.vca.vcloud_session.login(
                token=self.vca.vcloud_session.token)
            if not result:
                Log.debug(self.logger,
                          'vcloud session invalid, getting a new one')
                if self.vca.service_type in [VCA.VCA_SERVICE_TYPE_VCHS,
                                             'subscription']:
                    result = self.vca.login_to_org(self.instance, self.vca.org)
                elif self.vca.service_type in [VCA.VCA_SERVICE_TYPE_VCA,
                                               'ondemand']:
                    result = self.vca.login_to_instance_sso(self.instance)
                if result:
                    Log.debug(self.logger,
                              'successfully retrieved a new vcloud session')
                else:
                    raise Exception("Couldn't retrieve a new vcloud session")
            else:
                Log.debug(self.logger, 'vcloud session is valid')

    def re_login(self):
        if self.vca is None or \
           (self.vca.token is None and self.password is None):
            return False
        result = False
        try:
            Log.debug(self.logger,
                      'about to re-login with ' +
                      'host=%s type=%s token=%s org=%s' %
                      (self.vca.host, self.vca.service_type,
                       self.vca.token, self.vca.org))
            org_url = None if self.vca.vcloud_session is None else \
                self.vca.vcloud_session.org_url
            result = self.vca.login(token=self.vca.token,
                                    org=self.vca.org,
                                    org_url=org_url)
            if result:
                Log.debug(self.logger, 'vca.login with token successful')
                self.re_login_vcloud_session()
            else:
                Log.debug(self.logger, 'vca.login with token failed %s' %
                          self.vca.response.content)
                raise Exception('login with token failed')
        except Exception as e:
            Log.error(self.logger, str(e))
            tb = traceback.format_exc()
            Log.error(self.logger, tb)
            if self.password is not None and len(self.password) > 0:
                try:
                    Log.debug(self.logger, 'about to re-login with password')
                    result = self.vca.login(password=self.password,
                                            org=self.vca.org)
                    if result:
                        Log.debug(self.logger,
                                  'about to re-login vcloud_session')
                        self.re_login_vcloud_session()
                        Log.debug(self.logger,
                                  'after re-login vcloud_session')
                    self.save_config(self.profile, self.profile_file)
                except Exception:
                    return False
        return result

    def logout(self):
        assert self.vca is not None
        self.vca.logout()
        self.vca = None
        self.password = None
        self.instance = None
        self.host = None
        self.service_type = None
        self.version = None
        self.session_uri = None
        self.save_config(self.profile, self.profile_file)

    def org_to_table(self, vca):
        links = (vca.vcloud_session.organization.Link if
                 vca.vcloud_session.organization else [])
        org_name = (vca.vcloud_session.organization.name if
                    vca.vcloud_session.organization else [])
        org_id = (vca.vcloud_session.organization.id if
                  vca.vcloud_session.organization else [])
        table = [[details.get_type().split('.')[-1].split('+')[0],
                  details.get_name()] for details in
                 filter(lambda info: info.name, links)]
        table.append(['Org Id', org_id[org_id.rfind(':') + 1:]])
        table.append(['Org Name', org_name])
        sorted_table = sorted(
            table, key=operator.itemgetter(0), reverse=False)
        return sorted_table

    def vdc_to_table(self, vdc, gateways):
        table = []
        for entity in vdc.get_ResourceEntities().ResourceEntity:
            table.append([entity.type_.split('.')[-1].split('+')[0],
                         entity.name])
        for entity in vdc.get_AvailableNetworks().Network:
            table.append([entity.type_.split('.')[-1].split('+')[0],
                         entity.name])
        for entity in vdc.get_VdcStorageProfiles().VdcStorageProfile:
            table.append([entity.type_.split('.')[-1].split('+')[0],
                         entity.name])
        for gateway in gateways:
            table.append(['gateway', gateway.get_name()])
        sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)
        return sorted_table

    def vdc_resources_to_table(self, vdc):
        table = []
        computeCapacity = vdc.get_ComputeCapacity()
        cpu = computeCapacity.get_Cpu()
        memory = computeCapacity.get_Memory()
        # storageCapacity = vca.vdc.get_StorageCapacity()
        table.append(
            ['CPU (%s)' % cpu.get_Units(),
             cpu.get_Allocated(), cpu.get_Limit(),
             cpu.get_Reserved(), cpu.get_Used(),
             cpu.get_Overhead()])
        table.append(['Memory (%s)' % memory.get_Units(),
                      memory.get_Allocated(),
                      memory.get_Limit(), memory.get_Reserved(),
                      memory.get_Used(), memory.get_Overhead()])
        sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)
        return sorted_table

    def vapps_to_table(self, vdc):
        table = []
        if vdc is not None:
            for entity in vdc.get_ResourceEntities().ResourceEntity:
                if entity.type_ == 'application/vnd.vmware.vcloud.vApp+xml':
                    the_vapp = self.vca.get_vapp(vdc, entity.name)
                    vms = []
                    if the_vapp and the_vapp.me.Children:
                        for vm in the_vapp.me.Children.Vm:
                            vms.append(vm.name)
                    table.append([entity.name, utils.beautified(vms),
                                  self.vca.get_status(the_vapp.me.get_status()
                                                      ),
                                 'yes' if the_vapp.me.deployed
                                  else 'no', the_vapp.me.Description])
        sorted_table = sorted(table, key=operator.itemgetter(0),
                              reverse=False)
        return sorted_table

    def catalogs_to_table(self, catalogs):
        table = []
        for catalog in catalogs:
            if catalog.CatalogItems and catalog.CatalogItems.CatalogItem:
                for item in catalog.CatalogItems.CatalogItem:
                    table.append([catalog.name, item.name])
            else:
                table.append([catalog.name, ''])
        sorted_table = sorted(table, key=operator.itemgetter(0),
                              reverse=False)
        return sorted_table

    def vdc_template_to_table(self, templates):
        table = []
        if templates is None:
            return []
        for template in templates.get_VdcTemplate():
            table.append([template.get_name()])
        sorted_table = sorted(table, key=operator.itemgetter(0),
                              reverse=False)
        return sorted_table

    def vapp_details_to_table(self, vapp):
        table = []
        vms = []
        details = vapp.get_vms_details()
        for vm in details:
            vms.append(vm['name'])
        table.append(['vApp', 'name', vapp.name])
        table.append(['vApp', 'id', vapp.me.get_id().split(':')[-1]])
        table.append(['vApp', 'number of VMs', len(details)])
        table.append(['vApp', 'names of VMs', utils.beautified(vms)])

        for vm in details:
            for key in vm.keys():
                table.append(['VM', key, vm[key]])
        return table

    def disks_to_table(self, disks):
        table = []
        for disk in disks:
            if len(disk) > 0:
                table.append([disk[0].name,
                              int(disk[0].size) / self.DISK_SIZE,
                              disk[0].id,
                              disk[0].get_Owner().get_User()])
        sorted_table = sorted(table, key=operator.itemgetter(0),
                              reverse=False)
        return sorted_table

    def vms_to_table(self, vdc, vapp):
        table = []
        if vdc is not None:
            for entity in vdc.get_ResourceEntities().ResourceEntity:
                if entity.type_ == 'application/vnd.vmware.vcloud.vApp+xml':
                    if vapp is not None and \
                       vapp != '' and \
                       vapp != entity.name:
                        continue
                    the_vapp = self.vca.get_vapp(vdc, entity.name)
                    if (not the_vapp or not the_vapp.me or
                            not the_vapp.me.Children):
                        continue
                    for vm in the_vapp.me.Children.Vm:
                        owner = the_vapp.me.get_Owner().get_User().get_name()
                        vm_status = self.vca.get_status(vm.get_status())
                        sections = vm.get_Section()
                        virtualHardwareSection = (
                            filter(lambda section:
                                   section.__class__.__name__ ==
                                   "VirtualHardwareSection_Type",
                                   sections)[0])
                        items = virtualHardwareSection.get_Item()
                        cpu = (
                            filter(lambda item: item.get_Description().
                                   get_valueOf_() == "Number of Virtual CPUs",
                                   items)[0])
                        cpu_capacity = (
                            cpu.get_ElementName().get_valueOf_().
                            split(" virtual CPU(s)")[0])
                        memory = filter(lambda item: item.get_Description().
                                        get_valueOf_() == "Memory Size",
                                        items)[0]
                        memory_capacity = int(
                            memory.get_ElementName().get_valueOf_().
                            split(" MB of memory")[0]) / 1024
                        operatingSystemSection = (
                            filter(lambda section:
                                   section.__class__.__name__ ==
                                   "OperatingSystemSection_Type",
                                   sections)[0])
                        os = (operatingSystemSection.
                              get_Description().get_valueOf_())
                        ips = []
                        networks = []
                        cds = []
                        _url = '{http://www.vmware.com/vcloud/v1.5}ipAddress'
                        for item in items:
                            if item.Connection:
                                for c in item.Connection:
                                    networks.append(c.valueOf_)
                                    if c.anyAttributes_.get(
                                            _url):
                                        ips.append(c.anyAttributes_.get(
                                            _url))
                            elif (item.HostResource and
                                  item.ResourceSubType and
                                  item.ResourceSubType.valueOf_ ==
                                  'vmware.cdrom.iso'):
                                if len(item.HostResource[0].valueOf_) > 0:
                                    cds.append(item.HostResource[0].valueOf_)

                        networkConnectionSection = filter(
                            lambda section:
                                section.__class__.__name__ ==
                                "NetworkConnectionSectionType",
                            sections)[0]
                        networkConnectionSection \
                            .get_PrimaryNetworkConnectionIndex()
                        connections = networkConnectionSection \
                            .get_NetworkConnection()
                        macs = [connection.get_MACAddress() for connection
                                in connections]

                        table.append([vm.name, entity.name, vm_status,
                                      utils.beautified(ips),
                                      utils.beautified(macs),
                                      utils.beautified(networks),
                                      cpu_capacity,
                                      str(memory_capacity),
                                      utils.beautified(cds),
                                      os, owner])
        sorted_table = sorted(table, key=operator.itemgetter(0),
                              reverse=False)
        return sorted_table

    def select_default_gateway(self):
        gateways = self.vca.get_gateways(self.vdc_name)
        if len(gateways) > 0:
            self.gateway = gateways[0].get_name()
        else:
            self.gateway = None

    def gateways_to_table(self, gateways):
        table = []
        for gateway in gateways:
            interfaces = gateway.get_interfaces('uplink')
            ext_interface_table = []
            for interface in interfaces:
                ext_interface_table.append(interface.get_Name())
            interfaces = gateway.get_interfaces('internal')
            interface_table = []
            for interface in interfaces:
                interface_table.append(interface.get_Name())
            public_ips = gateway.get_public_ips()
            public_ips_value = public_ips
            if len(public_ips) > 2:
                public_ips_value = (
                    "vca gateway info - to list IPs (%d)"
                    % (len(public_ips)))
            table.append([
                gateway.get_name(),
                utils.beautified(str(public_ips_value)),
                'On' if gateway.is_dhcp_enabled() else 'Off',
                'On' if gateway.is_fw_enabled() else 'Off',
                'On' if gateway.is_nat_enabled() else 'Off',
                'On' if gateway.is_vpn_enabled() else 'Off',
                utils.beautified(interface_table),
                gateway.get_syslog_conf(),
                utils.beautified(ext_interface_table),
                '*' if gateway.get_name() == self.gateway else ' '
            ])
        sorted_table = sorted(table,
                              key=operator.itemgetter(0),
                              reverse=False)
        return sorted_table

    def gateway_to_table(self, gateway):
        table = []
        table.append(['Name', gateway.me.name])
        table.append(
            ['DCHP Service', 'On' if gateway.is_dhcp_enabled() else 'Off'])
        table.append(
            ['Firewall Service', 'On' if gateway.is_fw_enabled() else 'Off'])
        table.append(
            ['NAT Service', 'On' if gateway.is_nat_enabled() else 'Off'])
        table.append(
            ['VPN Service', 'On' if gateway.is_vpn_enabled() else 'Off'])
        table.append(
            ['Syslog', gateway.get_syslog_conf()])
        public_ips = gateway.get_public_ips()
        table.append(
            ['External IP #', len(public_ips)])
        if len(public_ips) > 6:
            table.append([
                'External IPs',
                utils.beautified(public_ips[0:6])])
            table.append([
                'External IPs',
                utils.beautified(public_ips[6:])])
        else:
            table.append([
                'External IPs',
                utils.beautified(public_ips)])
        interfaces = gateway.get_interfaces('uplink')
        ext_interface_table = []
        for interface in interfaces:
            ext_interface_table.append(interface.get_Name())
        table.append(
            ['Uplinks',
             utils.beautified(ext_interface_table)])
        return table

    def networks_to_table(self, networks):
        table = []
        for item in networks:
            dhcp_pools = []
            if item.get_ServiceConfig() and len(
                    item.get_ServiceConfig().get_NetworkService()) > 0:
                for service in item.get_ServiceConfig().get_NetworkService():
                    if service.original_tagname_ == 'GatewayDhcpService':
                        for p in service.get_Pool():
                            if p.get_IsEnabled():
                                dhcp_pools.append(p.get_LowIpAddress() +
                                                  '-' + p.get_HighIpAddress())
            config = item.get_Configuration()
            gateways = []
            netmasks = []
            ranges = []
            dns1 = []
            dns2 = []
            for scope in config.get_IpScopes().get_IpScope():
                gateways.append(scope.get_Gateway())
                netmasks.append(scope.get_Netmask())
                if scope.get_Dns1() is not None:
                    dns1.append(scope.get_Dns1())
                if scope.get_Dns2() is not None:
                    dns2.append(scope.get_Dns2())
                if scope.get_IpRanges() is not None:
                    for r in scope.get_IpRanges().get_IpRange():
                        ranges.append(r.get_StartAddress() + '-' +
                                      r.get_EndAddress())
            table.append([
                item.get_name(),
                config.get_FenceMode(),
                utils.beautified(gateways),
                utils.beautified(netmasks),
                utils.beautified(dns1),
                utils.beautified(dns2),
                utils.beautified(ranges)
            ])
        sorted_table = sorted(table,
                              key=operator.itemgetter(0),
                              reverse=False)
        return sorted_table

    def firewall_rules_to_table(self, gateway):
        def create_protocol_string(protocol):
            if protocol.get_Any():
                return 'any'
            protocols = []
            if protocol.get_Tcp():
                protocols.append('tcp')
            if protocol.get_Udp():
                protocols.append('udp')
            if protocol.get_Icmp():
                protocols.append('icmp')
            if protocol.get_Other():
                protocols.append('other')
            return utils.beautified(protocols)
        table = []
        for rule in gateway.get_fw_rules():
            table.append([rule.get_Description(),
                          rule.get_SourceIp(),
                          rule.get_SourcePortRange(),
                          rule.get_DestinationIp(),
                          rule.get_DestinationPortRange(),
                          create_protocol_string(rule.get_Protocols()),
                          'On' if rule.get_IsEnabled() == 1 else 'Off'])
        sorted_table = sorted(table,
                              key=operator.itemgetter(0),
                              reverse=False)
        return sorted_table

    def dhcp_to_table(self, gateway):
        table = []
        service = gateway.get_dhcp_service()
        if service is None:
            return table
        for pool in gateway.get_dhcp_pools():
            table.append([
                pool.get_Network().get_name(),
                pool.get_LowIpAddress(),
                pool.get_HighIpAddress(),
                'Yes' if pool.get_IsEnabled() == 1 else 'No',
                pool.get_DefaultLeaseTime(),
                pool.get_MaxLeaseTime()
            ])
        sorted_table = sorted(table,
                              key=operator.itemgetter(0),
                              reverse=False)
        return sorted_table

    def nat_rules_to_table(self, gateway):
        table = []
        rules = gateway.get_nat_rules()
        if rules is None:
            return table
        for natRule in rules:
            ruleId = natRule.get_Id()
            enable = natRule.get_IsEnabled()
            ruleType = natRule.get_RuleType()
            gatewayNatRule = natRule.get_GatewayNatRule()
            originalIp = gatewayNatRule.get_OriginalIp()
            originalPort = gatewayNatRule.get_OriginalPort()
            translatedIp = gatewayNatRule.get_TranslatedIp()
            translatedPort = gatewayNatRule.get_TranslatedPort()
            protocol = gatewayNatRule.get_Protocol()
            interface = gatewayNatRule.get_Interface().get_name()
            table.append([ruleId, str(enable), ruleType, originalIp,
                          "any" if not originalPort else originalPort,
                          translatedIp,
                          "any" if not translatedPort else translatedPort,
                          "any" if not protocol else protocol, interface])
        return table

    def vpn_endpoints_to_table(self, gateway):
        table = []
        service = gateway.get_vpn_service()
        if service is None:
            return table
        for endpoint in service.get_Endpoint():
            network = ''
            for interface in gateway.get_interfaces('uplink'):
                endpint_ref = endpoint.get_Network().get_href()
                if_ref = interface.get_Network().get_href()
                if endpint_ref == if_ref:
                    network = interface.get_Network().get_name()
            ip = endpoint.get_PublicIp()
            table.append([network, ip])
        return table

    def vpn_tunnels_to_table(self, gateway):
        table = []
        service = gateway.get_vpn_service()
        if service is None:
            return table
        for tunnel in service.get_Tunnel():
            local_networks = []
            for network in tunnel.get_LocalSubnet():
                local_networks.append(network.get_Name())
            peer_networks = []
            for network in tunnel.get_PeerSubnet():
                peer_networks.append(network.get_Name())
            table.append([tunnel.get_Name(),
                          tunnel.get_LocalIpAddress(),
                          utils.beautified(local_networks),
                          tunnel.get_PeerIpAddress(),
                          utils.beautified(peer_networks),
                          'Yes' if tunnel.get_IsEnabled() == 1 else 'No',
                          'Yes' if tunnel.get_IsOperational() == 1 else 'No'])
        return table
