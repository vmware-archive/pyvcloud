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


import os
import operator
import ConfigParser
from cryptography.fernet import Fernet
from pyvcloud.vcloudair import VCA
from pyvcloud.vcloudsession import VCS
from pyvcloud import _get_logger, Log


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
        self.org = None
        self.logger = _get_logger() if debug else None

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
        self.vca = VCA(host=host, username=user,
                       service_type=service_type, version=version,
                       verify=self.verify, log=self.debug)
        self.password = password
        self.vca.token = token
        self.instance = instance
        self.org = org
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
            # vcloud_session.login(token=session_token)
            self.vca.vcloud_session = vcloud_session
        Log.debug(self.logger, 'restored vca %s' % self.vca)
        if self.vca.vcloud_session is not None:
            Log.debug(self.logger, 'restored vcloud_session %s' %
                      self.vca.vcloud_session)
            if self.vca.vcloud_session.token is not None:
                Log.debug(self.logger, 'restored vcloud_session token %s' %
                          self.vca.vcloud_session.token)

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
        if self.org is None:
            self.config.remove_option(section, 'org')
        else:
            self.config.set(section, 'org', self.org)
        if self.vca is None or self.vca.vcloud_session is None:
            self.config.remove_option(section, 'org_url')
            self.config.remove_option(section, 'session_token')
            self.config.remove_option(section, 'session_uri')
        else:
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
        with open(os.path.expanduser(profile_file), 'w+') as configfile:
            self.config.write(configfile)

    def login(self, host, username, password, version, save_password=True):
        self.vca = VCA(host=host, username=username, version=version,
                       verify=self.verify, log=self.debug)
        service_type = self.vca.get_service_type()
        if service_type == VCA.VCA_SERVICE_TYPE_UNKNOWN:
            raise Exception('service type unknown')
        self.vca.service_type = service_type
        result = self.vca.login(password=password)
#        todo: evaluate if vca requires get instances or
#        get services upon login....
#        if not, remove for speed
        if result:
            if save_password:
                self.password = password
            self.save_config(self.profile, self.profile_file)
        return result

# todo: consider VCA and STANDALONE also (done VCHS)
    def re_login_vcloud_session(self):
        Log.debug(self.logger, 'about to re-login vca =%s' % self.vca)
        if self.vca.vcloud_session is not None:
            Log.debug(self.logger, 'about to re-login vcloud_session =%s' %
                      self.vca.vcloud_session)
            if self.vca.vcloud_session.token is not None:
                Log.debug(self.logger,
                          'about to re-login vcloud_session token =%s' %
                          self.vca.vcloud_session.token)
        if self.vca.vcloud_session is not None and \
           self.vca.vcloud_session.token is not None:
            result = self.vca.vcloud_session.login(
                token=self.vca.vcloud_session.token)
            if not result:
                Log.debug(self.logger,
                          'vcloud session invalid, getting a new one')
                result = self.vca.login_to_org(self.instance, self.org)
                if result:
                    Log.debug(self.logger,
                              'successfully retrieved a new vcloud session')
                else:
                    raise Exception("Couldn't retrieve a new vcloud session")
            else:
                Log.debug(self.logger, 'vcloud session is valid')

# todo: consider VCA and STANDALONE also (done VCHS)
    def re_login(self):
        if self.vca is None or \
           (self.vca.token is None and self.password is None):
            return False
        result = False
        try:
            Log.debug(self.logger, 'about to re-login with token=%s' %
                      self.vca.token)
            result = self.vca.login(token=self.vca.token)
            if result:
                Log.debug(self.logger, 'vca.login with token successful')
                self.re_login_vcloud_session()
            else:
                raise Exception('login with token failed')
        except Exception:
            if self.password is not None and len(self.password) > 0:
                try:
                    Log.debug(self.logger, 'about to re-login with password')
                    result = self.vca.login(password=self.password)
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
        self.vca = None
        self.password = None
        self.instance = None
        self.org = None
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
