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
                 debug=False, insecure=False):
        self.profile = profile
        self.profile_file = profile_file
        self.debug = debug
        self.verify = not insecure
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
        section = 'Profile-%s' % self.profile
        if self.config.has_section(section):
            host = None
            user = None
            password = None
            token = None
            service_type = None
            version = None
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
            self.vca.password = password
            self.vca.token = token

    def save_config(self, profile='default', profile_file='~/.vcarc'):
        with open(os.path.expanduser(profile_file), 'w+') as configfile:
            self.config.write(configfile)

    def login(self, host, username, password, version):
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
            pass
#            save config
        return result

    def logout(self):
        pass
