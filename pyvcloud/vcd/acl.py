# VMware vCloud Director Python SDK
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.utils import get_admin_href


class Acl(object):
    def __init__(self, client, resource):
        """
            Constructor for Acl objects.
            :param client: (pyvcloud.vcd.client): The client.
            :param resource: (lxml.objectify.ObjectifiedElement): XML 
            representation of the entity in which acl belongs to.
            """  # NOQA
        self.client = client
        self.resource = resource

    def add_access_settings(self, access_settings_list=None):
        """
        Add acl to resource.
        :param access_settings_list: (list of dict): list of access_setting
            in the dict format. Each dict contains:
            type: (str): type of the subject. One of 'org' or 'user'.
            name: (str): name of the user or org.
            access_level: (str): access_level of the particular subject. One of
            'ReadOnly', 'Change', 'FullControl'
            eg. [{'name': 'user', 'type': 'user1', 'access_level': 'Change'},
            {'name': 'org1', 'type': 'org', 'access_level': 'ReadOnly'}]
        :return:  A :class:`lxml.objectify.StringElement` object representing
            the updated access control setting of the resource.
        """  # NOQA
        control_access_params = self.client.get_linked_resource(
            self.resource, RelationType.DOWN,
            EntityType.CONTROL_ACCESS_PARAMS.value)

        # if access_settings_list is None, nothing to add.
        if access_settings_list is not None:
            # get the current access settings for the particular resource
            old_access_settings_params = None
            if hasattr(control_access_params, 'AccessSettings'):
                old_access_settings_params = control_access_params. \
                    AccessSettings

                # discard the AccessSettings fro control_access_params as we
                #  will be constructing a new one based on access_settings_list
                control_access_params.remove(old_access_settings_params)

            # remove common access_setting between access_settings_list
            # and old_access_settings_params
            for access_setting in list(access_settings_list):
                subject_name = access_setting['name']
                subject_type = access_setting['type']
                matched_access_setting = \
                    self.search_for_access_setting_by_subject(
                        subject_name, subject_type,
                        old_access_settings_params)
                if matched_access_setting is not None:
                    old_access_settings_params.remove(matched_access_setting)

            new_access_settings_params = \
                self.convert_access_settings_list_to_params(
                    access_settings_list)

            # combine the new and old access settings
            if hasattr(old_access_settings_params, 'AccessSetting'):
                for old_access_setting in list(
                        old_access_settings_params.AccessSetting):
                    new_access_settings_params.append(old_access_setting)

            control_access_params.append(new_access_settings_params)

            return self.client.post_linked_resource(
                self.resource, RelationType.CONTROL_ACCESS,
                EntityType.CONTROL_ACCESS_PARAMS.value, control_access_params)

        return control_access_params

    def remove_access_settings(self,
                               access_settings_list=None,
                               remove_all=False):
        """
        Remove acl from resource.
        :param access_settings_list: (list of dict): list of access_setting
            in the dict format. Each dict contains:
            type: (str): type of the subject. One of 'org' or 'user'.
            name: (str): name of the user or org.
            eg. [{'name': 'user', 'type': 'user1'},
            {'name': 'org1', 'type': 'org']
            :param remove_all: (bool) : True if all the acl of the resource
            should be removed.
        :return:  A :class:`lxml.objectify.StringElement` object representing
            the updated access control setting of the resource.
        """  # NOQA
        control_access_params = self.client.get_linked_resource(
            self.resource, RelationType.DOWN,
            EntityType.CONTROL_ACCESS_PARAMS.value)

        # get the current access settings for the particular resource
        old_access_settings_params = None
        if hasattr(control_access_params, 'AccessSettings'):
            old_access_settings_params = control_access_params.AccessSettings

            # discard the AccessSettings from control_access_params as we
            # will be constructing a new one based on access_settings_list
            control_access_params.remove(old_access_settings_params)

        # if remove_all is True, nothing to remove from
        # old_access_settings_params. AccessSettings is already discarded
        # from control_access_params
        if remove_all is False:
            # remove common AccessSetting between access_settings_list
            # and old_access_settings_params
            for access_setting in list(access_settings_list):
                subject_name = access_setting['name']
                subject_type = access_setting['type']
                matched_access_setting = \
                    self.search_for_access_setting_by_subject(
                        subject_name, subject_type,
                        old_access_settings_params)
                if matched_access_setting is None:
                    raise Exception(
                        'Subject \'%s:%s\' not found in the '
                        'existing acl' % (subject_type, subject_name))
                else:
                    old_access_settings_params.remove(matched_access_setting)
            # appending the the modified old_access_settings_params to
            # control_access_params if at least 1 AccessSetting exist in it.
            if hasattr(old_access_settings_params, 'AccessSetting'):
                control_access_params.append(old_access_settings_params)

        return self.client.post_linked_resource(
            self.resource, RelationType.CONTROL_ACCESS,
            EntityType.CONTROL_ACCESS_PARAMS.value, control_access_params)

    def share_access(self, everyone_access_level='ReadOnly'):
        """
        Share the resource to all members of the organization with a 
        particular access level.
        :param everyone_access_level: (str) : access level when sharing the
            resource with everyone. One of 'ReadOnly', 'Change', 'FullControl'
        :return:  A :class:`lxml.objectify.StringElement` object representing
            the updated access control setting of the resource.
        """  # NOQA
        control_access_params = self.client.get_linked_resource(
            self.resource, RelationType.DOWN,
            EntityType.CONTROL_ACCESS_PARAMS.value)

        control_access_params['IsSharedToEveryone'] = \
            E.IsSharedToEveryone(True)
        if everyone_access_level is not None:
            if hasattr(control_access_params, 'EveryoneAccessLevel'):
                control_access_params['EveryoneAccessLevel'] = \
                    E.EveryoneAccessLevel(everyone_access_level)
            else:
                # EveryoneAccessLevel should be just after IsSharedToEveryone
                # (first element) in case there are any AccessSettings
                control_access_params.insert(1, E.EveryoneAccessLevel(
                    everyone_access_level))

        return self.client.post_linked_resource(
            self.resource, RelationType.CONTROL_ACCESS,
            EntityType.CONTROL_ACCESS_PARAMS.value, control_access_params)

    def unshare_access(self):
        """
        Unshare the resource from all members of current organization
        :return:  A :class:`lxml.objectify.StringElement` object representing
            the updated access control setting of the resource.
        """  # NOQA
        control_access_params = self.client.get_linked_resource(
            self.resource, RelationType.DOWN,
            EntityType.CONTROL_ACCESS_PARAMS.value)

        control_access_params['IsSharedToEveryone'] = \
            E.IsSharedToEveryone(False)
        # EveryoneAccessLevel should not exist when
        # IsSharedToEveryone is false
        if hasattr(control_access_params, 'EveryoneAccessLevel'):
            everyone_access_level = getattr(control_access_params,
                                            'EveryoneAccessLevel')
            control_access_params.remove(everyone_access_level)

        return self.client.post_linked_resource(
            self.resource, RelationType.CONTROL_ACCESS,
            EntityType.CONTROL_ACCESS_PARAMS.value, control_access_params)

    def convert_access_settings_list_to_params(self, access_settings_list):
        """ Convert access_settings_list to xml object of type
        AccessSettingsType
        :param access_settings_list: (list of dict): list of access_setting
            in the dict format. Each dict contains:
            type: (str): type of the subject. One of 'org' or 'user'
            name: (str): subject name
            access_level: (str): access_level of each subject. One of
            'ReadOnly', 'Change', 'FullControl'.
            eg. [{'name': 'user', 'type': 'user1', 'access_level': 'Change'},
            {'name': 'org1', 'type': 'org', 'access_level': 'ReadOnly'}]
        :return: A :class:`lxml.objectify.StringElement` object
        representing xml of type AccessSettingsType
        """  # NOQA
        access_settings_params = E.AccessSettings()
        for access_setting in access_settings_list:
            if access_setting["type"] == 'user':
                org_href = find_link(self.resource, RelationType.UP,
                                     EntityType.ORG.value).href
                subject_href = self.client.get_user_in_org(
                    access_setting['name'],
                    org_href).get('href')
                subject_name = access_setting['name']
                subject_type = EntityType.USER.value
            else:
                subject_href = get_admin_href(
                    self.client.get_org_by_name(
                        access_setting['name']).get(
                        'href'))
                subject_name = access_setting['name']
                subject_type = EntityType.ADMIN_ORG.value

            access_setting_params = E.AccessSetting(
                E.Subject(name=subject_name,
                          href=subject_href,
                          type=subject_type),
                E.AccessLevel(access_setting['access_level'])
            )
            access_settings_params.append(access_setting_params)
        return access_settings_params

    @staticmethod
    def search_for_access_setting_by_subject(subject_name,
                                             subject_type,
                                             access_settings_params):
        """
        Search for a particular AccessSetting object based on the subject name
        and type
        :param subject_name: (str): name of the subject
        :param subject_type: (str): type of the subject. One of 'org', 'user'
        :param access_settings_params: (lxml.objectify.StringElement):
            AccessSettings xml object which needs to searched by subject.
        :return:  A :class:`lxml.objectify.StringElement` object
            representing a access setting matching the given subject.
        """  # NOQA
        subject_type_to_entity_dict = {'user': EntityType.USER.value,
                                       'org': EntityType.ADMIN_ORG.value}
        if hasattr(access_settings_params, 'AccessSetting'):
            for access_setting_params in \
                    access_settings_params.AccessSetting:
                # if the subject name and type matches with the
                # access_setting_params, return it.
                if (access_setting_params.Subject.attrib['name'].lower()
                    == subject_name.lower()) and \
                        (access_setting_params.Subject.attrib['type'] ==
                         subject_type_to_entity_dict[subject_type]):
                    return access_setting_params
        return None
