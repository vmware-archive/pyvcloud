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
import ConfigParser
from cryptography.fernet import Fernet
from pyvcloud.vcloudair import VCA


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
        self.vca = VCA(host=host, username=user,
                       service_type=service_type, version=version,
                       verify=self.verify, log=self.debug)
        self.password = password
        self.vca.token = token

    def save_config(self, profile='default', profile_file='~/.vcarc'):
        section = 'Global'
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, 'profile', profile)
        section = 'Profile-%s' % profile
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, 'host', self.vca.host)
        if self.vca.username is None:
            self.config.remove_option(section, 'user')
        else:
            self.config.set(section, 'user', self.vca.username)
        self.config.set(section, 'service_type', self.vca.service_type)
        self.config.set(section, 'service_version', self.vca.version)
        if self.vca.token is None:
            self.config.remove_option(section, 'token')
        else:
            self.config.set(section, 'token', self.vca.token)
        if self.password is not None and len(self.password) > 0:
            cipher_suite = Fernet(self.crypto_key)
            cipher_text = cipher_suite.encrypt(self.password.encode('utf-8'))
            self.config.set(section, 'password', cipher_text)
        else:
            self.config.remove_option(section, 'password')
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

    def re_login(self):
        if self.vca is None or \
           (self.vca.token is None and self.password is None):
            return False
        result = False
        try:
            result = self.vca.login(token=self.vca.token)
            if not result:
                raise Exception('login with token failed')
        except Exception:
            if self.password is not None and len(self.password) > 0:
                try:
                    result = self.vca.login(password=self.password)
                    self.save_config(self.profile, self.profile_file)
                except Exception:
                    return False
        return result

    def logout(self):
        assert self.vca is not None
        self.vca.username = None
        self.vca.token = None
        self.password = None
        self.save_config(self.profile, self.profile_file)
