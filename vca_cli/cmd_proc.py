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


import traceback
import os
import operator
import ConfigParser
from cryptography.fernet import Fernet
from pyvcloud.vcloudair import VCA
from pyvcloud.vcloudsession import VCS
from pyvcloud import _get_logger, Log
from vca_cli_utils import VcaCliUtils


utils = VcaCliUtils()


class CmdProc:
    crypto_key = 'l1ZLY5hYPu4s2IXkTVxtndJ-L_k16rP1odagwhP_DsY='

    def __init__(self, profile=None, profile_file=None,
                 json_output=False, xml_output=False,
                 debug=False, insecure=False):
        self.profile = profile
        self.profile_file = profile_file
        self.debug = debug
        self.verify = not insecure
        self.json_output = json_output
        self.xml_output = xml_output
        self.password = None
        self.config = ConfigParser.RawConfigParser()
        self.vca = None
        self.instance = None
        self.logger = _get_logger() if debug else None
        self.error_message = None

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
        if self.config.has_section(section):
            if self.config.has_option(section, 'host'):
                host = self.config.get(section, 'host')
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
            self.vca.vdc = vdc
        Log.debug(self.logger, 'restored vca %s' % self.vca)
        if self.vca.vcloud_session is not None:
            Log.debug(self.logger, 'restored vcloud_session %s' %
                      self.vca.vcloud_session)
            Log.debug(self.logger, 'restored org=%s' % self.vca.org)
            if self.vca.vcloud_session.token is not None:
                Log.debug(self.logger, 'restored vcloud_session token %s' %
                          self.vca.vcloud_session.token)

    def print_profile_file(self):
        headers = ['Profile', 'Selected', 'Host', 'Type', 'User',
                   'Instance', 'Org', 'vdc']
        table = []
        for section in self.config.sections():
            if section.startswith('Profile-'):
                section_name = section.split('-')[1]
                selected = '*' if section_name == self.profile else ''
                host = self.config.get(section, 'host') \
                    if self.config.has_option(section, 'host') else ''
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
            if self.vca.vdc is None:
                self.config.remove_option(section, 'vdc')
            else:
                self.config.set(section, 'vdc', self.vca.vdc)
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

# TODO: add other gw services
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
                    "%d IPs (list = 'vca gateway -g %s info')"
                    % (len(public_ips), gateway.get_name()))
            table.append([
                gateway.get_name(),
                str(public_ips_value).strip('[]').replace("'", ""),
                'On' if gateway.is_dhcp_enabled() else 'Off',
                'On' if gateway.is_fw_enabled() else 'Off',
                'On' if gateway.is_nat_enabled() else 'Off',
                'On' if gateway.is_vpn_enabled() else 'Off',
                utils.beautified(interface_table),
                gateway.get_syslog_conf(),
                utils.beautified(ext_interface_table)
            ])
        sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)
        return sorted_table
