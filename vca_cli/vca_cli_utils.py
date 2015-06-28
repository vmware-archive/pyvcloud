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


import ConfigParser
import json
import click
from cryptography.fernet import Fernet


class VcaCliUtils:
    properties = ['session_token', 'org', 'org_url',
                  'service', 'vdc', 'instance',
                  'service_type', 'service_version',
                  'token', 'user', 'host', 'gateway',
                  'session_uri', 'verify', 'password', 'host_score']
    crypto_key = 'l1ZLY5hYPu4s2IXkTVxtndJ-L_k16rP1odagwhP_DsY='

    def __init__(self):
        pass

    def load_context(self, ctx, profile, profile_file):
        config = ConfigParser.RawConfigParser()
        config.read(profile_file)
        ctx.obj = {}
        if profile != '':
            ctx.obj['profile'] = profile
        else:
            section = 'Global'
            if config.has_option(section, 'profile'):
                ctx.obj['profile'] = config.get(section, 'profile')
            else:
                ctx.obj['profile'] = 'default'
        section = 'Profile-%s' % ctx.obj['profile']
        for prop in self.properties:
            ctx.obj[prop] = (config.get(section, prop)
                             if config.has_option(section, prop) else '')
            if ctx.obj[prop] == 'None':
                ctx.obj[prop] = None
            if ctx.obj[prop] == 'True':
                ctx.obj[prop] = True
            if ctx.obj[prop] == 'False':
                ctx.obj[prop] = False
            if prop == 'password' and ctx.obj[prop] and len(ctx.obj[prop]) > 0:
                cipher_suite = Fernet(self.crypto_key)
                ctx.obj[prop] = cipher_suite.decrypt(ctx.obj[prop])
        # ctx.obj['verify'] = not insecure
        # ctx.obj['json_output'] = json_output
        # ctx.obj['xml_output'] = xml_output
        # ctx.obj['debug'] = False

    def save_context(self, ctx, profile, profile_file):
        config = ConfigParser.RawConfigParser()
        section = 'Profile-%s' % profile
        if not config.has_section(section):
            config.add_section(section)
        for prop in self.properties:
            value = ctx.obj[prop]
            if prop == 'password' and value and len(value) > 0:
                cipher_suite = Fernet(self.crypto_key)
                cipher_text = cipher_suite.encrypt(value.encode('utf-8'))
                config.set(section, prop, cipher_text)
            else:
                config.set(section, prop, value)
        section = 'Global'
        prop = 'profile'
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, prop, profile)
        with open(profile_file, 'w+') as configfile:
            config.write(configfile)

    def print_warning(self, msg, ctx):
        if (ctx is not None and ctx.obj is not
                None and ctx.obj['json_output']):
            json_msg = {"Returncode": "1", "Details": msg}
            print(json.dumps(json_msg, sort_keys=True,
                             indent=4, separators=(',', ': ')))
        else:
            click.secho(msg, fg='yellow')
