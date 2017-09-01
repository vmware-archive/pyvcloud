# vCloud CLI 0.1
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
import yaml

VCD_CLI_USER_PATH = '~/.vcd-cli'
PROFILE_PATH = VCD_CLI_USER_PATH + '/profiles.yaml'


class Profiles(object):

    def __init__(self):
        self.path = None
        self.data = None

    @staticmethod
    def load(path=PROFILE_PATH):
        try:
            profile_path = os.path.expanduser(path)
            p = Profiles()
            p.data = {'active': None}
            with open(profile_path, 'r') as f:
                p.data = yaml.load(f)
        except Exception:
            pass
        p.path = profile_path
        return p

    def save(self):
        try:
            parent_dir = os.path.dirname(self.path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            stream = open(self.path, 'w')
            yaml.dump(self.data, stream, default_flow_style=False)
        except Exception:
            import traceback
            traceback.print_exc()

    def update(self, host, org, user, token, api_version, wkep, verify,
               disable_warnings, vdc, org_href, vdc_href,
               log_request, log_header, log_body, name='default'):
        if self.data is None:
            self.data = {}
        if 'profiles' not in self.data:
            self.data['profiles'] = []
        profile = {}
        profile['name'] = str(name)
        profile['host'] = str(host)
        profile['org'] = str(org)
        profile['user'] = str(user)
        profile['token'] = str(token)
        profile['api_version'] = str(api_version)
        profile['verify'] = verify
        profile['log_request'] = log_request
        profile['log_header'] = log_header
        profile['log_body'] = log_body
        profile['disable_warnings'] = disable_warnings
        profile['wkep'] = wkep
        profile['org_in_use'] = str(org)
        profile['vdc_in_use'] = str(vdc)
        profile['org_href'] = str(org_href)
        profile['vdc_href'] = str(vdc_href)
        tmp = [profile]
        for p in self.data['profiles']:
            if p['name'] != name:
                tmp.append(p)
        self.data['profiles'] = tmp
        self.data['active'] = str(name)
        self.save()

    def get(self, prop, name='default', default=None):
        value = None
        if 'profiles' in self.data.keys():
            for p in self.data['profiles']:
                if p['name'] == name:
                    if prop in p:
                        value = p[prop]
                    else:
                        value = default
        return value

    def set(self, prop, value, name='default'):
        if 'profiles' not in self.data.keys():
            self.data['profiles'] = {}
        for p in self.data['profiles']:
            if p['name'] == name:
                p[prop] = value
                self.save()
                break
