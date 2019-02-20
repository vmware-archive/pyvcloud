# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
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

from enum import Enum
import logging
import warnings

import requests

from helpers.portgroup_helper import PortgroupHelper
from pyvcloud.system_test_framework.constants.gateway_constants import \
    GatewayConstants
from pyvcloud.system_test_framework.constants.ovdc_network_constant import \
    OvdcNetConstants
from pyvcloud.system_test_framework.vapp_constants import VAppConstants
from pyvcloud.system_test_framework.utils import create_vapp_from_template

from pyvcloud.vcd.client import ApiVersion
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.external_network import ExternalNetwork
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.system import System
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.utils import cidr_to_netmask


def developerModeAware(function):
    """Decorator function to skip execution of decorated function.

    To be used on test teardown methods.

    :param function function: decorated function.

    :return: a function that either executes the decorated function or skips
        it, based on the value of a particular param in the environment
        configuration.

    :rtype: function
    """

    def wrapper(self):
        if not Environment._config['global']['developer_mode']:
            function(self)
        else:
            Environment.get_default_logger().debug(
                'Skipping ' + function.__name__ +
                ' because developer mode is on.')

    return wrapper


class CommonRoles(Enum):
    CATALOG_AUTHOR = 'Catalog Author'
    CONSOLE_ACCESS_ONLY = 'Console Access Only'
    ORGANIZATION_ADMINISTRATOR = 'Organization Administrator'
    VAPP_AUTHOR = 'vApp Author'
    VAPP_USER = 'vApp User'


class Environment(object):
    _config = None
    _logger = None

    _sys_admin_client = None
    _pvdc_href = None
    _pvdc_name = None
    _external_network_href = None
    _external_network_name = None
    _org_href = None
    _ovdc_href = None
    _vapp_href = None
    _portgroupType = "DV_PORTGROUP"

    _user_name_for_roles = {
        CommonRoles.CATALOG_AUTHOR: 'catalog_author',
        CommonRoles.CONSOLE_ACCESS_ONLY: 'console_user',
        CommonRoles.ORGANIZATION_ADMINISTRATOR: 'org_admin',
        CommonRoles.VAPP_AUTHOR: 'vapp_author',
        CommonRoles.VAPP_USER: 'vapp_user'
    }

    _user_href_for_user_names = {}

    @classmethod
    def init(cls, config_data):
        """Initializer for Environment class.

        :param object config_data: a PyYAML object that contains the yaml
            representation of configuration data read from the configuration
            file.
        """
        cls._config = config_data
        if not cls._config['connection']['verify'] and \
           cls._config['connection']['disable_ssl_warnings']:
            requests.packages.urllib3.disable_warnings()
        cls._logger = cls.get_default_logger()

    @classmethod
    def get_config(cls):
        """Get test configuration parameter dictionary.

        :return: a dict containing configuration information.

        :rtype: dict
        """
        return cls._config

    @classmethod
    def get_default_logger(cls):
        """Get a handle to the logger for system_tests.

        :return: default logger instance.

        :rtype: logging.Logger
        """
        if cls._logger is None:
            cls._logger = logging.getLogger('pyvcloud.system_tests')
            cls._logger.setLevel(logging.DEBUG)
            if not cls._logger.handlers:
                log_file = cls._config['logging']['default_log_filename']
                if log_file is not None:
                    handler = logging.FileHandler(log_file)
                else:
                    handler = logging.NullHandler()
                formatter = logging.Formatter('%(asctime)-23.23s | '
                                              '%(levelname)-5.5s | '
                                              '%(name)-15.15s | '
                                              '%(module)-15.15s | '
                                              '%(funcName)-30.30s | '
                                              '%(message)s')
                handler.setFormatter(formatter)
                cls._logger.addHandler(handler)
        return cls._logger

    @classmethod
    def _basic_check(cls):
        """Does basic sanity check for configuration and sys admin client.

        :raises: Exception: if the basic configuration is missing.
        """
        if cls._config is None:
            raise Exception('Missing base configuration.')
        if cls._sys_admin_client is None:
            cls._sys_admin_client = cls.get_sys_admin_client()

    @classmethod
    def get_sys_admin_client(cls):
        """Creates a sys admin client.

        :return: a sys admin client.

        :rtype: pyvcloud.vcd.client.Client

        :raises: Exception: if the basic configuration is missing.
        """
        if cls._config is None:
            raise Exception('Missing base configuration.')

        org = cls._config['vcd']['sys_org_name']
        password = cls._config['vcd']['sys_admin_pass']
        username = cls._config['vcd']['sys_admin_username']
        return cls.get_client(org=org, username=username, password=password)

    @classmethod
    def get_client_in_default_org(cls, role):
        """Returns a client.

        The client is for a user in the default test organization who has the
        specified role.

        :param CommonRoles role: role of the user.

        :return: a client configured with a user of the specified role logged
            in.

        :rtype: pyvcloud.vcd.client.Client

        :raises: Exception: if the basic configuration is missing.
        """
        if cls._config is None:
            raise Exception('Missing base configuration.')

        org = cls._config['vcd']['default_org_name']
        username = cls._user_name_for_roles[role]
        password = cls._config['vcd']['default_org_user_password']

        return cls.get_client(org=org, username=username, password=password)

    @classmethod
    def get_client(cls, org, username, password):
        """Returns a client for a particular user.

        The user is identified by the specified username-password combo in a
        given organization.

        :param str org:  name of the organization, which the user belongs to.
        :param str username: username of the user.
        :param str password: password of the user.

        :return: a client.

        :rtype: pyvcloud.vcd.client.Client

        :raises: Exception: if the basic configuration is missing.
        """
        if cls._config is None:
            raise Exception('Missing base configuration.')

        client = Client(
            cls._config['vcd']['host'],
            api_version=cls._config['vcd']['api_version'],
            verify_ssl_certs=cls._config['connection']['verify'],
            log_file=cls._config['logging']['default_client_log_filename'],
            log_requests=cls._config['logging']['log_requests'],
            log_headers=cls._config['logging']['log_headers'],
            log_bodies=cls._config['logging']['log_bodies'])

        client.set_credentials(BasicLoginCredentials(username, org, password))

        return client

    @classmethod
    def attach_vc(cls):
        """Attaches VC and NSX to vCD as per configuration file.

        If VC is already attached no further action is taken.
        """
        cls._basic_check()
        platform = Platform(cls._sys_admin_client)
        vc_name = cls._config['vc']['vcenter_host_name']
        for record in platform.list_vcenters():
            if record.get('name').lower() == vc_name.lower():
                cls._logger.debug(vc_name + ' is already attached.')
                return
        platform.attach_vcenter(
            vc_server_name=vc_name,
            vc_server_host=cls._config['vc']['vcenter_host_ip'],
            vc_admin_user=cls._config['vc']['vcenter_admin_username'],
            vc_admin_pwd=cls._config['vc']['vcenter_admin_password'],
            nsx_server_name=cls._config['nsx']['nsx_hostname'],
            nsx_host=cls._config['nsx']['nsx_host_ip'],
            nsx_admin_user=cls._config['nsx']['nsx_admin_username'],
            nsx_admin_pwd=cls._config['nsx']['nsx_admin_password'],
            is_enabled=True)

    @classmethod
    def create_pvdc(cls):
        """Creates a pvdc by the name specified in the config file.

        Skips creating one, if such a pvdc already exists. Also stores the
        href and name of the provider vdc as class variables for future use.
        """
        cls._basic_check()
        pvdc_name = cls._config['vcd']['default_pvdc_name']

        system = System(
            cls._sys_admin_client,
            admin_resource=cls._sys_admin_client.get_admin())

        pvdc_refs = system.list_provider_vdcs()
        if pvdc_name is not '*':
            for pvdc_ref in pvdc_refs:
                if pvdc_ref.get('name').lower() == pvdc_name.lower():
                    cls._logger.debug('Reusing existing ' + pvdc_name)
                    cls._pvdc_href = pvdc_ref.get('href')
                    cls._pvdc_name = pvdc_name
                    return
            cls._logger.debug('Creating new pvdc' + pvdc_name)
            # TODO(VCDA-603) : use create pvdc code
        else:
            if len(pvdc_refs) > 0:
                cls._logger.debug('Defaulting to first pvdc in the system : ' +
                                  pvdc_refs[0].get('name'))
                cls._pvdc_href = pvdc_refs[0].get('href')
                cls._pvdc_name = pvdc_refs[0].get('name')
            else:
                cls._logger.debug('No usable pVDC found. Aborting test.')
                raise Exception('Test Aborted. No usable pVDC.')

    @classmethod
    def _create_external_network(cls):
        vc_name = cls._config['vc']['vcenter_host_name']
        portgrouphelper = PortgroupHelper(cls._sys_admin_client)
        port_group = portgrouphelper.get_available_portgroup_name(
            vc_name, Environment._portgroupType)

        if port_group is None:
            raise Exception(
                'None of the port groups are free for new network.')

        ext_config = cls._config['external_network']
        ip_scopes = cls._config['external_network']['ip_scopes']
        if len(ip_scopes) == 0:
            raise Exception('No network spec provided.')
        # [{subnet:'10.10.10.1/24', ip_range:'10.10.10.101-10.10.10.150'}]
        primary_subnet = ip_scopes[0]['subnet']
        gateway_ip, prefix_len = primary_subnet.split('/')
        netmask = cidr_to_netmask(primary_subnet)[1]
        ip_ranges = ip_scopes[0]['ip_ranges']
        primary_dns_ip = '8.8.8.8'
        secondary_dns_ip = '8.8.8.9'
        dns_suffix = 'example.com'
        platform = Platform(cls._sys_admin_client)
        ext_net = platform.create_external_network(
            name=ext_config['name'],
            vim_server_name=vc_name,
            port_group_names=[port_group],
            gateway_ip=gateway_ip,
            netmask=netmask,
            ip_ranges=ip_ranges,
            description=ext_config['name'],
            primary_dns_ip=primary_dns_ip,
            secondary_dns_ip=secondary_dns_ip,
            dns_suffix=dns_suffix)

        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        cls._sys_admin_client.get_task_monitor().wait_for_success(task=task)
        return ext_net

    @classmethod
    def create_external_network(cls):
        """Creates an external network by the name specified in the config file.

        Skips creating one, if such a network already exists. Also stores the
        href and name of the network as class variables for future use.
        """
        cls._basic_check()
        net_name = cls._config['external_network']['name']

        platform = Platform(cls._sys_admin_client)

        net_refs = platform.list_external_networks()
        if net_name is not '*':
            for net_ref in net_refs:
                if net_ref.get('name').lower() == net_name.lower():
                    cls._logger.debug('Reusing existing ' + net_name)
                    cls._external_network_href = net_ref.get('href')
                    cls._external_network_name = net_name
                    return
            cls._logger.debug('Creating new external network' + net_name)
            ext_nw = cls._create_external_network()
            cls._external_network_href = ext_nw.get('href')
            cls._external_network_name = net_name
            cls._logger.debug('Created external network ' + net_name)
        else:
            if len(net_refs) > 0:
                cls._logger.debug('Defaulting to first network : ' +
                                  net_refs[0].get('name'))
                cls._external_network_href = net_refs[0].get('href')
                cls._external_network_name = net_refs[0].get('name')
            else:
                cls._logger.debug('No usable network found. Aborting test.')
                raise Exception('Test Aborted. No usable external network.')

    @classmethod
    def create_org(cls):
        """Creates an org by the name specified in the config file.

        Skips creating one, if such an org already exists. Also stores the
        href of the org as class variable for future use.
        """
        cls._basic_check()
        system = System(
            cls._sys_admin_client,
            admin_resource=cls._sys_admin_client.get_admin())
        org_name = cls._config['vcd']['default_org_name']
        org_resource_list = cls._sys_admin_client.get_org_list()
        for org_resource in org_resource_list:
            if org_resource.get('name').lower() == org_name.lower():
                cls._logger.debug('Reusing existing org ' + org_name + '.')
                cls._org_href = org_resource.get('href')
                return
        cls._logger.debug('Creating new org ' + org_name)
        system.create_org(
            org_name=org_name, full_org_name=org_name, is_enabled=True)
        # The following contraption is required to get the non admin href of
        # the org. The result of create_org() contains the admin version of
        # the href, since we created the org as a sys admin.
        org_resource = cls._sys_admin_client.get_org_by_name(org_name)
        cls._org_href = org_resource.get('href')

    @classmethod
    def create_users(cls):
        """Creates users for each of the roles in CommonRoles.

        Skips creating users which are already present in the organization.

        :raises: Exception: if the class variable _org_href is not populated.
        """
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        org = Org(cls._sys_admin_client, href=cls._org_href)
        for role_enum in cls._user_name_for_roles.keys():
            user_name = cls._user_name_for_roles[role_enum]
            user_records = list(
                org.list_users(name_filter=('name', user_name)))
            if len(user_records) > 0:
                cls._logger.debug('Reusing existing user ' + user_name + '.')
                cls._user_href_for_user_names[user_name] = \
                    user_records[0].get('href')
                continue
            role = org.get_role_record(role_enum.value)
            cls._logger.debug('Creating user ' + user_name + '.')
            user_resource = org.create_user(
                user_name=user_name,
                password=cls._config['vcd']['default_org_user_password'],
                role_href=role.get('href'),
                is_enabled=True)

            cls._user_href_for_user_names[user_name] = \
                user_resource.get('href')

    @classmethod
    def create_ovdc(cls):
        """Creates an org vdc with the name specified in the config file.

        Skips creating one, if such an org vdc already exists. Also stores the
        href of the org vdc as class variable for future use.

        :raises: Exception: if the class variable _org_href or _pvdc_name
            is not populated.
        """
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        if cls._pvdc_name is None:
            raise Exception('pVDC ' + cls._config['vcd']['default_pvdc_name'] +
                            ' doesn\'t exist.')

        org = Org(cls._sys_admin_client, href=cls._org_href)
        ovdc_name = cls._config['vcd']['default_ovdc_name']
        for vdc in org.list_vdcs():
            if vdc.get('name').lower() == ovdc_name.lower():
                cls._logger.debug('Reusing existing ovdc ' + ovdc_name + '.')
                cls._ovdc_href = vdc.get('href')
                return

        storage_profiles = [{
            'name':
            cls._config['vcd']['default_storage_profile_name'],
            'enabled':
            True,
            'units':
            'MB',
            'limit':
            0,
            'default':
            True
        }]

        system = System(
            cls._sys_admin_client,
            admin_resource=cls._sys_admin_client.get_admin())
        netpool_to_use = cls._get_netpool_name_to_use(system)

        cls._logger.debug('Creating ovdc ' + ovdc_name + '.')
        vdc_resource = org.create_org_vdc(
            ovdc_name,
            cls._pvdc_name,
            network_pool_name=netpool_to_use,
            network_quota=cls._config['vcd']['default_network_quota'],
            storage_profiles=storage_profiles,
            uses_fast_provisioning=True,
            is_thin_provision=True)

        cls._sys_admin_client.get_task_monitor().wait_for_success(
            task=vdc_resource.Tasks.Task[0])

        org.reload()
        # The following contraption is required to get the non admin href of
        # the ovdc. vdc_resource contains the admin version of the href since
        # we created the ovdc as a sys admin.
        for vdc in org.list_vdcs():
            if vdc.get('name').lower() == ovdc_name.lower():
                cls._ovdc_href = vdc.get('href')

    @classmethod
    def _get_netpool_name_to_use(cls, system):
        """Fetches the name of the netpool that will be used by org vdc.

        Defaults to the first netpool in the system if * is specified.

        :param pyvcloud.vcd.system.System system: a System object.

        :return: name of the netpool to use.

        :rtype: str
        """
        netpools = system.list_network_pools()
        netpool_to_use = None
        netpool_name = cls._config['vcd']['default_netpool_name']
        if netpool_name is not '*':
            for item in netpools:
                if item.get('name').lower() == netpool_name.lower():
                    netpool_to_use = item.get('name')
                    break

        if netpool_to_use is None:
            cls._logger.debug('Using first netpool in system : ' +
                              netpools[0].get('name'))
            netpool_to_use = netpools[0].get('name')

        return netpool_to_use

    @classmethod
    def create_ovdc_network(cls):
        """Creates an isolated org vdc network.

        The name of the created org vdc network is specified in the
        configuration file, skips creating one, if such a network already
        exists.

        :raises: Exception: if the class variable _ovdc_href is not populated.
        """
        cls._basic_check()
        if cls._ovdc_href is None:
            raise Exception('OrgVDC ' +
                            cls._config['vcd']['default_ovdc_name'] +
                            ' doesn\'t exist.')

        vdc = VDC(cls._sys_admin_client, href=cls._ovdc_href)
        expected_net_name = cls._config['vcd']['default_ovdc_network_name']
        records_dict = vdc.list_orgvdc_network_records()

        for net_name in records_dict.keys():
            if net_name.lower() == expected_net_name.lower():
                cls._logger.debug('Reusing existing org-vdc network ' +
                                  expected_net_name)
                return

        cls._logger.debug('Creating org-vdc network ' + expected_net_name)
        result = vdc.create_isolated_vdc_network(
            network_name=expected_net_name,
            network_cidr=cls._config['vcd']
            ['default_ovdc_network_network_cidr'])

        cls._sys_admin_client.get_task_monitor()\
            .wait_for_success(task=result.Tasks.Task[0])

    @classmethod
    def create_direct_ovdc_network(cls):
        """Creates a direct org vdc network.

        The name of the created org vdc network is specified in the
        configuration file, skips creating one, if such a network already
        exists.

        :raises: Exception: if the class variable _ovdc_href is not populated.
        """
        cls._basic_check()
        if cls._ovdc_href is None:
            raise Exception('OrgVDC ' +
                            cls._config['vcd']['default_ovdc_name'] +
                            ' doesn\'t exist.')

        vdc = VDC(cls._sys_admin_client, href=cls._ovdc_href)
        expected_net_name = cls._config['vcd'][
            'default_direct ovdc_network_name']
        records_dict = vdc.list_orgvdc_network_records()

        for net_name in records_dict.keys():
            if net_name.lower() == expected_net_name.lower():
                cls._logger.debug('Reusing existing direct org-vdc network ' +
                                  expected_net_name)
                return

        cls._logger.debug('Creating direct org-vdc network ' +
                          expected_net_name)
        result = vdc.create_directly_connected_vdc_network(
            network_name=expected_net_name,
            parent_network_name=cls._config['external_network']['name'],
            description='direct org vdc network',
            is_shared=False)

        cls._sys_admin_client.get_task_monitor()\
            .wait_for_success(task=result.Tasks.Task[0])

    @classmethod
    def create_routed_ovdc_network(cls):
        """Creates a routed org vdc network.

        The name of the created org vdc network is specified in the
        ovdc_network_constant file, skips creating one, if such a network already
        exists.

        :raises: Exception: if the class variable _ovdc_href is not populated.
        """
        cls._basic_check()
        if cls._ovdc_href is None:
            raise Exception('OrgVDC ' +
                            cls._config['vcd']['default_ovdc_name'] +
                            ' doesn\'t exist.')

        vdc = VDC(cls._sys_admin_client, href=cls._ovdc_href)

        expected_net_name = OvdcNetConstants.routed_net_name
        records_dict = vdc.list_orgvdc_network_records()

        for net_name in records_dict.keys():
            if net_name.lower() == expected_net_name.lower():
                cls._logger.debug('Reusing existing direct org-vdc network ' +
                                  expected_net_name)
                return

        result = vdc.create_routed_vdc_network(
            network_name=OvdcNetConstants.routed_net_name,
            gateway_name=GatewayConstants.name,
            network_cidr=OvdcNetConstants.routed_orgvdc_network_gateway_ip,
            description='org vdc network description')

        cls._sys_admin_client.get_task_monitor() \
            .wait_for_success(task=result.Tasks.Task[0])

    @classmethod
    def create_catalog(cls):
        """Creates a catalog by the name specified in the configuration  file.

        Skips creating one, if such a catalog already exists.

        :raises: Exception: if the class variable _org_href is not populated.
        """
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        try:
            catalog_author_client = Environment.get_client_in_default_org(
                CommonRoles.CATALOG_AUTHOR)
            org = Org(catalog_author_client, href=cls._org_href)
            catalog_name = cls._config['vcd']['default_catalog_name']
            catalog_records = org.list_catalogs()
            for catalog_record in catalog_records:
                if catalog_record.get('name') == catalog_name:
                    cls._logger.debug('Reusing existing catalog ' +
                                      catalog_name)
                    return

            cls._logger.debug('Creating new catalog ' + catalog_name)
            catalog_resource = org.create_catalog(
                name=catalog_name, description='')
            catalog_author_client.get_task_monitor().wait_for_success(
                task=catalog_resource.Tasks.Task[0])
        finally:
            catalog_author_client.logout()

    @classmethod
    def share_catalog(cls):
        """Shares the test catalog with all members in the test organization.

        :raises: Exception: if the class variable _org_href is not populated.
        :raises: EntityNotFoundException: if the catalog in question is
            missing.
        """
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        try:
            catalog_author_client = Environment.get_client_in_default_org(
                CommonRoles.CATALOG_AUTHOR)
            org = Org(catalog_author_client, href=cls._org_href)
            catalog_name = cls._config['vcd']['default_catalog_name']
            catalog_records = org.list_catalogs()
            for catalog_record in catalog_records:
                if catalog_record.get('name') == catalog_name:
                    cls._logger.debug('Sharing catalog ' + catalog_name + ' to'
                                      ' all members of org ' + org.get_name())
                    org.share_catalog_with_org_members(
                        catalog_name=catalog_name)
                    return
            raise EntityNotFoundException('Catalog ' + catalog_name +
                                          'doesn\'t exist.')
        finally:
            catalog_author_client.logout()

    @classmethod
    def upload_template(cls):
        """Uploads the test template to the test catalog.

        If template already exists in the catalog then skips uploading it.

        :raises: Exception: if the class variable _org_href is not populated.
        """
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        try:
            catalog_author_client = Environment.get_client_in_default_org(
                CommonRoles.CATALOG_AUTHOR)
            org = Org(catalog_author_client, href=cls._org_href)

            catalog_name = cls._config['vcd']['default_catalog_name']
            catalog_items = org.list_catalog_items(catalog_name)
            template_name = cls._config['vcd']['default_template_file_name']
            for item in catalog_items:
                if item.get('name').lower() == template_name.lower():
                    cls._logger.debug('Reusing existing template ' +
                                      template_name)
                    return

            cls._logger.debug('Uploading template ' + template_name +
                              ' to catalog ' + catalog_name + '.')
            org.upload_ovf(catalog_name=catalog_name, file_name=template_name)

            # wait for the template import to finish in vCD.
            catalog_item = org.get_catalog_item(
                name=catalog_name, item_name=template_name)
            template = catalog_author_client.get_resource(
                catalog_item.Entity.get('href'))
            catalog_author_client.get_task_monitor().wait_for_success(
                task=template.Tasks.Task[0])
        finally:
            catalog_author_client.logout()

    @classmethod
    def cleanup(cls):
        """Cleans up the various class variables."""
        if cls._sys_admin_client is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)  # NOQA
                cls._sys_admin_client.logout()
                cls._sys_admin_client = None
                cls._pvdc_href = None
                cls._pvdc_name = None
                cls._external_network_href = None
                cls._external_network_name = None
                cls._org_href = None
                cls._ovdc_href = None
                cls._vapp_href = None

    @classmethod
    def get_test_pvdc_name(cls):
        """Gets the name of the pvdc to be used for testing.

        Can return None if the method create_pvdc hasn't be called before
        invoking this method.

        :return: name of the pvdc to be used for testing.

        :rtype: str
        """
        return cls._pvdc_name

    @classmethod
    def get_test_external_network(cls, client):
        """Gets the external used for testing.

        :param pyvcloud.vcd.client.Client client: client which will be used to
            create the External Network object.

        :return: the organization in which all tests will run.

        :rtype: pyvcloud.vcd.external_network.ExternalNetwork
        """
        return ExternalNetwork(client, href=cls._external_network_href)

    @classmethod
    def get_test_org(cls, client):
        """Gets the organization used for testing.

        :param pyvcloud.vcd.client.Client client: client which will be used to
            create the Org object.

        :return: the organization in which all tests will run.

        :rtype: pyvcloud.vcd.org.Org
        """
        return Org(client, href=cls._org_href)

    @classmethod
    def get_test_vdc(cls, client):
        """Gets the vdc for testing.

        :param pyvcloud.vcd.client.Client client: client which will be used to
            create the VDC object.

        :return: the vdc that is backing the organization in which all tests
            will run.

        :rtype: pyvcloud.vcd.vdc.VDC
        """
        return VDC(client, href=cls._ovdc_href)

    @classmethod
    def get_test_vapp_with_network(cls, client):
        """Gets the vapp for testing in current vDC.

        :param pyvcloud.vcd.client.Client client: client which will be used to
            create the VDC object.

        :return: the vdc that is backing the organization in which all tests
            will run.

        :rtype: pyvcloud.vcd.vdc.VDC
        """
        if not cls._vapp_href:
            vdc = Environment.get_test_vdc(client)
            try:
                vapp = vdc.get_vapp(VAppConstants.name)
                cls._vapp_href = vapp.get('href')
            except EntityNotFoundException:
                cls._vapp_href = create_vapp_from_template(
                    client,
                    vdc,
                    VAppConstants.name,
                    cls._config['vcd']['default_catalog_name'],
                    cls._config['vcd']['default_template_file_name'],
                    power_on=False,
                    deploy=False)
                vapp = VApp(client, href=cls._vapp_href)
                vapp.create_vapp_network(
                    VAppConstants.network1_name,
                    VAppConstants.network1_cidr,
                    ip_ranges=VAppConstants.network1_ip_ranges)
        return VApp(client, href=cls._vapp_href)

    @classmethod
    def get_username_for_role_in_test_org(cls, role_name):
        """Gets the username of the user in the test org with particular role.

        :param str role_name: name of the role which the concerned user has.

        :return: username of the concerned user.

        :rtype: str
        """
        return cls._user_name_for_roles[role_name]

    @classmethod
    def get_user_href_in_test_org(cls, user_name):
        """Gets href of an user in the test organization.

        :param str user_name: name of the user whose href needs to be
            retrieved.

        :return: href of the user.

        :rtype: str
        """
        return cls._user_href_for_user_names[user_name]

    @classmethod
    def get_default_catalog_name(cls):
        """Get the name of the default catalog that will be used for testing.

        :return: name of the test catalog.

        :rtype: str
        """
        return cls._config['vcd']['default_catalog_name']

    @classmethod
    def get_default_template_name(cls):
        """Get the name of the default template that will be used for testing.

        :return: name of the test template.

        :rtype: str
        """
        return cls._config['vcd']['default_template_file_name']

    @classmethod
    def get_default_orgvdc_network_name(cls):
        """Get the name of the default org vdc network for testing.

        :return: name of the org vdc network.

        :rtype: str
        """
        return cls._config['vcd']['default_ovdc_network_name']

    @classmethod
    def get_vapp_in_test_vdc(cls, client, vapp_name):
        """Gets the vApp identified by it's name in the current org vdc.

        :param pyvcloud.vcd.client.Client client: client which will be used to
            create the VApp object.

        :param str vapp_name: name of the vApp which needs to be retrieved.

        :return: the requested vApp.

        :rtype: pyvcloud.vcd.vapp.VApp
        """
        vdc = cls.get_test_vdc(client)
        vapp_resource = vdc.get_vapp(vapp_name)
        return VApp(client, resource=vapp_resource)

    @classmethod
    def create_advanced_gateway(cls):
        """Creates a gateway."""

        cls._basic_check()
        _gateway = None
        try:
            _gateway = cls.get_test_gateway(cls._sys_admin_client)
        except EntityNotFoundException:
            pass

        if _gateway is None:
            ext_config = cls._config['external_network']
            vdc = cls.get_test_vdc(cls._sys_admin_client)
            api_version = cls._config['vcd']['api_version']
            if float(api_version) <= float(ApiVersion.VERSION_30.value):
                gateway = vdc.create_gateway_api_version_30(
                    GatewayConstants.name, [ext_config['name']])
            elif float(api_version) == float(ApiVersion.VERSION_31.value):
                gateway = vdc.create_gateway_api_version_31(
                    GatewayConstants.name, [ext_config['name']],
                    should_create_as_advanced=True)
            elif float(api_version) >= float(ApiVersion.VERSION_32.value):
                gateway = vdc.create_gateway_api_version_32(
                    GatewayConstants.name, [ext_config['name']],
                    should_create_as_advanced=True)

            cls._sys_admin_client.get_task_monitor().wait_for_success(
                task=gateway.Tasks.Task[0])

    @classmethod
    def get_test_gateway(cls, client):
        """Gets gateway by name.

        :param pyvcloud.vcd.client.Client client: client which will be used
        to create the VDC object.

        :return: gateway.

        :rtype: pyvcloud.vcd.gateway gateway
        """
        vdc = cls.get_test_vdc(client)
        return vdc.get_gateway(GatewayConstants.name)
