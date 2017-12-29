# vCloud CLI 0.1
#
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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

from vcd_cli.profiles import Profiles


def load_user_plugins():
    profiles = Profiles.load()
    if 'extensions' in profiles.data and len(profiles.data) > 0:
        for extension in profiles.data['extensions']:
            __import__(extension)
