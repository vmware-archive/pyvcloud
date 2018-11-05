# VMware vCloud Director Python SDK
# Copyright (c) 2017-2018 VMware, Inc. All Rights Reserved.
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
from copy import deepcopy

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.utils import get_admin_href


class Acl(object):
    def __init__(self, client, parent_resource, resource=None):
        """Constructor for Acl object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param lxml.objectify.ObjectifiedElement parent_resource: object
            containing XML representation of the parent entity whose Access
            Control List this object operates on.
        :param lxml.objectify.ObjectifiedElement resource: object
            containing EntityType.CONTROL_ACCESS_PARAMS XML data representing
            the Access Control List of the parent object.
        """
        self.client = client
        self.parent_resource = parent_resource
        self.resource = resource

    def get_resource(self):
        """Fetches the XML representation of the Access Control List from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.CONTROL_ACCESS_PARAMS XML data
            representing the concerned Access Control List.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_linked_resource(
                self.parent_resource, RelationType.DOWN,
                EntityType.CONTROL_ACCESS_PARAMS.value)
        return self.resource

    def update_resource(self, control_access_params):
        """Update the access control settings of the parent resource.

        :param lxml.objectify.ObjectifiedElement control_access_params: object
            containing EntityType.CONTROL_ACCESS_PARAMS XML data representing
            the updated Access Control List.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data that represents the updated Access Control List of the parent
            resource.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        # vdc Acl is updated though PUT instead of POST
        if self.parent_resource.attrib.get('type') == EntityType.VDC.value:
            self.resource = self.client. \
                put_linked_resource(self.parent_resource,
                                    RelationType.CONTROL_ACCESS,
                                    EntityType.CONTROL_ACCESS_PARAMS.value,
                                    control_access_params)
        else:
            self.resource = self.client. \
                post_linked_resource(self.parent_resource,
                                     RelationType.CONTROL_ACCESS,
                                     EntityType.CONTROL_ACCESS_PARAMS.value,
                                     control_access_params)
        return self.resource

    def get_access_settings(self):
        """Get the Access Control List of the parent resource.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data that represents the Access Control List of the parent
            resource.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self.get_resource()

    def add_access_settings(self, access_settings_list=None):
        """Add access settings.

        Append new / Overwrite old access setting(s) to the existing Access
        Control List of the parent resource.

        :param list access_settings_list: list of dictionaries, where each
            dictionary represents a single access setting. The dictionary
            structure is as follows,

            - type: (str): type of the subject. One of 'org' or 'user'.
            - name: (str): name of the user or org.
            - access_level: (str): access_level of the particular subject.
                Allowed values are 'ReadOnly', 'Change' or 'FullControl'.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated Access Control List of the resource.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.resource = self.get_resource()

        # if access_settings_list is None, nothing to add.
        if access_settings_list is None:
            return self.resource

        control_access_params = deepcopy(self.resource)
        # get the current access settings of the parent resource
        old_access_settings_params = None
        if hasattr(control_access_params, 'AccessSettings'):
            old_access_settings_params = control_access_params. \
                AccessSettings

            # discard the AccessSettings from control_access_params as we
            #  will be constructing a new one based on access_settings_list
            control_access_params.remove(old_access_settings_params)

        # remove common access_setting between access_settings_list
        # and old_access_settings_params
        for access_setting in access_settings_list:
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
        return self.update_resource(control_access_params)

    def remove_access_settings(self,
                               access_settings_list=None,
                               remove_all=False):
        """Remove access settings.

        Remove a list of access settings from the existing Access Control List
        of the parent resource.

        :param list access_settings_list: list of dictionaries, where each
            dictionary represents a single access setting. The dictionary
            structure is as follows,

            - type: (str): type of the subject. One of 'org' or 'user'.
            - name: (str): name of the user or org.
        :param bool remove_all: True, if the entire Access Control List of the
            parent resource should be removed, else False.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated access control setting of the
            resource.

        :rtype: lxml.objectify.ObjectifiedElement`
        """
        self.resource = self.get_resource()

        # if access_settings_list is None and remove_all is False, nothing to
        # remove.
        if access_settings_list is None and remove_all is False:
            return self.resource

        control_access_params = deepcopy(self.resource)
        # get the current access settings from parent resource
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
            for access_setting in access_settings_list:
                subject_name = access_setting['name']
                subject_type = access_setting['type']
                matched_access_setting = \
                    self.search_for_access_setting_by_subject(
                        subject_name, subject_type,
                        old_access_settings_params)
                if matched_access_setting is None:
                    raise EntityNotFoundException('Subject \'%s:%s\' not '
                                                  'found in the '
                                                  'existing Acl' %
                                                  (subject_type, subject_name))
                else:
                    old_access_settings_params.remove(matched_access_setting)
            # appending the the modified old_access_settings_params to
            # control_access_params if at least 1 AccessSetting exist in
            # old_access_settings_params.
            if hasattr(old_access_settings_params, 'AccessSetting'):
                control_access_params.append(old_access_settings_params)

        return self.update_resource(control_access_params)

    def share_with_org_members(self, everyone_access_level='ReadOnly'):
        """Share the resource to all members of the organization.

        :param str everyone_access_level: level of access granted while
            sharing the resource with everyone. Allowed values are 'ReadOnly',
            'Change', or 'FullControl'. Default value is 'ReadOnly'.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated access control setting of the
            resource.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.resource = self.get_resource()

        control_access_params = deepcopy(self.resource)

        control_access_params['IsSharedToEveryone'] = \
            E.IsSharedToEveryone(True)
        if everyone_access_level is not None:
            if hasattr(control_access_params, 'EveryoneAccessLevel'):
                control_access_params['EveryoneAccessLevel'] = \
                    E.EveryoneAccessLevel(everyone_access_level)
            else:
                # EveryoneAccessLevel should be just after IsSharedToEveryone
                # (first element) in case there are any AccessSettings
                control_access_params.insert(
                    1, E.EveryoneAccessLevel(everyone_access_level))

        return self.update_resource(control_access_params)

    def unshare_from_org_members(self):
        """Unshare the resource from all members of current organization.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated access control setting of the
            resource.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.resource = self.get_resource()

        control_access_params = deepcopy(self.resource)

        control_access_params['IsSharedToEveryone'] = \
            E.IsSharedToEveryone(False)
        # EveryoneAccessLevel should not exist when
        # IsSharedToEveryone is false
        if hasattr(control_access_params, 'EveryoneAccessLevel'):
            everyone_access_level = control_access_params.EveryoneAccessLevel
            control_access_params.remove(everyone_access_level)

        return self.update_resource(control_access_params)

    def convert_access_settings_list_to_params(self, access_settings_list):
        """Convert access settings from one format to other.

        Convert dictionary representation of access settings to AccessSettings
        XML element. Please refer to schema definition of
        EntityType.CONTROL_ACCESS_PARAMS for more details.

        :param list access_settings_list: list of dictionaries, where each
            dictionary represents a single access setting. The dictionary
            structure is as follows,

            - type: (str): type of the subject. One of 'org' or 'user'.
            - name: (str): name of the user or org.
            - access_level: (str): access_level of the particular subject.
                Allowed values are 'ReadOnly', 'Change' or 'FullControl'.

        :return: an object containing AccessSettings XML data.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        access_settings_params = E.AccessSettings()
        for access_setting in access_settings_list:
            if access_setting["type"] == 'user':
                org_href = self.get_org_href()
                subject_href = self.client.get_user_in_org(
                    access_setting['name'], org_href).get('href')
                subject_type = EntityType.USER.value
            elif access_setting["type"] == 'org':
                subject_href = get_admin_href(
                    self.client.get_org_by_name(
                        access_setting['name']).get('href'))
                subject_type = EntityType.ADMIN_ORG.value
            else:
                raise InvalidParameterException("Invalid subject type")

            subject_name = access_setting['name']
            # Make 'ReadOnly' the default access_level if it is not specified.
            if 'access_level' in access_setting:
                access_level = access_setting['access_level']
            else:
                access_level = 'ReadOnly'
            access_setting_params = E.AccessSetting(
                E.Subject(
                    name=subject_name, href=subject_href, type=subject_type),
                E.AccessLevel(access_level))
            access_settings_params.append(access_setting_params)
        return access_settings_params

    def get_org_href(self):
        """Return the href of the org where the parent resource belongs to.

        :return: href of the org to which the parent resource belongs.

        :rtype: str
        """
        if 'VApp' in self.parent_resource.tag:
            # for vapp, have to get the org via vdc
            vdc_href = find_link(self.parent_resource, RelationType.UP,
                                 EntityType.VDC.value).href
            return find_link(
                self.client.get_resource(vdc_href), RelationType.UP,
                EntityType.ORG.value).href
        else:
            return find_link(self.parent_resource, RelationType.UP,
                             EntityType.ORG.value).href

    @staticmethod
    def search_for_access_setting_by_subject(subject_name, subject_type,
                                             access_settings_params):
        """Search an AccessSettings object for a particular AccessSetting.

        The search is based on the subject name and type.

        :param str subject_name: name of the subject.
        :param str subject_type: type of the subject. Value must be either
            'org' or 'user'.
        :param lxml.objectify.ObjectifiedElement access_settings_params:
            an object containing AccessSettings XML data.

        :return: an object containing AccessSetting XML data representing the
            matched access setting. Please refer to schema definition of
            EntityType.CONTROL_ACCESS_PARAMS for more details.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        subject_type_to_entity_dict = {
            'user': EntityType.USER.value,
            'org': EntityType.ADMIN_ORG.value
        }
        if hasattr(access_settings_params, 'AccessSetting'):
            for access_setting_params in \
                    access_settings_params.AccessSetting:
                # if the subject name and type matches with the
                # access_setting_params, return it.
                name = access_setting_params.Subject.attrib['name']
                type = access_setting_params.Subject.attrib['type']
                if (name.lower() == subject_name.lower()) and \
                        (type == subject_type_to_entity_dict[subject_type]):
                    return access_setting_params
        return None
