import warnings

import requests

from flufl.enum import Enum

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.system import System


def developerModeAware(function):
    def wrapper(self):
        if not Environment._config['global']['developer_mode']:
            function(self)
        else:
            print('Skipping ' + function.__name__ +
                  ' because deveopler mode is on.')
    return wrapper


class CommonRoles(Enum):
    CATALOG_AUTHOR = 'Catalog Author'
    CONSOLE_ACCESS_ONLY = 'Console Access Only'
    ORGANIZATION_ADMINISTRATOR = 'Organization Administrator'
    SYS_ADMIN = 'System Administrator'
    VAPP_AUTHOR = 'vApp Author'
    VAPP_USER = 'vApp User'
    CUSTOM_ROLE = ''


class Environment(object):
    _config = None
    _sys_admin_client = None
    _pvdc_href = None
    _pvdc_name = None
    _org_href = None
    _ovdc_href = None
    # Don't add sys admin to this dictionary
    _user_name_for_roles = {
        CommonRoles.CATALOG_AUTHOR: 'catalog_author',
        CommonRoles.CONSOLE_ACCESS_ONLY: 'console_user',
        CommonRoles.ORGANIZATION_ADMINISTRATOR: 'org_admin',
        CommonRoles.VAPP_AUTHOR: 'vapp_author',
        CommonRoles.VAPP_USER: 'vapp_user'}

    @classmethod
    def init(cls, config_data):
        cls._config = config_data
        if not cls._config['rest']['verify'] and \
           cls._config['rest']['disable_ssl_warnings']:
            requests.packages.urllib3.disable_warnings()

    @classmethod
    def _basic_check(cls):
        if cls._config is None:
            raise Exception('Missing base configuration.')
        if cls._sys_admin_client is None:
            cls.get_sys_admin_client()

    @classmethod
    def get_sys_admin_client(cls):
        if cls._config is None:
            raise Exception('Missing base configuration.')
        if cls._sys_admin_client is None:
            cls._sys_admin_client = cls.get_client(CommonRoles.SYS_ADMIN)

        return cls._sys_admin_client

    @classmethod
    def get_client(cls, role, org=None, username=None, password=None):
        if cls._config is None:
            raise Exception('Missing base configuration.')

        client = Client(
            cls._config['vcd']['host'],
            api_version=cls._config['vcd']['api_version'],
            verify_ssl_certs=cls._config['rest']['verify'],
            log_file=cls._config['logging']['default_log_filename'],
            log_requests=cls._config['logging']['log_requests'],
            log_headers=cls._config['logging']['log_headers'],
            log_bodies=cls._config['logging']['log_bodies'])

        if org is None or username is None or password is None:
            org = cls._config['vcd']['default_org_name']
            password = cls._config['vcd']['default_org_user_password']
            username = None
            if role is CommonRoles.SYS_ADMIN:
                org = cls._config['vcd']['sys_org_name']
                password = cls._config['vcd']['sys_admin_pass']
                username = cls._config['vcd']['sys_admin_username']
            else:
                username = cls._user_name_for_roles[role]

        client.set_credentials(BasicLoginCredentials(username, org, password))

        return client

    @classmethod
    def attach_vc(cls):
        cls._basic_check()
        platform = Platform(cls._sys_admin_client)
        vc_name = cls._config['vc']['vcenter_host_name']
        for record in platform.list_vcenters():
            if record.get('name') == vc_name:
                print(vc_name + ' is already attached.')
                return
        # Untested code
        platform.attach_vcenter(
            vc_server_name=cls._config['vc']['vcenter_host_name'],
            vc_server_host=cls._config['vc']['vcenter_host_ip'],
            vc_admin_user=cls._config['vc']['vcenter_admin_username'],
            vc_admin_pwd=cls._config['vc']['vcenter_admin_password'],
            nsx_server_name=cls._config['nsx']['nsx_hostname'],
            nsx_host=cls._config['nsx']['nsx_host_ip'],
            nsx_admin_user=cls._config['nsx']['nsx_admin_username'],
            nsx_admin_pwd=cls._config['nsx']['nsx_admin_password'],
            is_enabled=True)
        # TODO wait for async task to finish

    @classmethod
    def create_pvdc(cls):
        cls._basic_check()
        pvdc_name = cls._config['vcd']['default_pvdc_name']

        system = System(cls._sys_admin_client,
                        admin_resource=cls._sys_admin_client.get_admin())

        pvdc_refs = system.list_provider_vdcs()
        if pvdc_name is not '*':
            for pvdc_ref in pvdc_refs:
                if pvdc_ref.get('name') == pvdc_name:
                    print('Resusing existing ' + pvdc_name)
                    cls._pvdc_href = pvdc_ref.get('href')
                    cls._pvdc_name = pvdc_name
                    return
            print('Creating new pvdc' + pvdc_name)
            # TODO : use create pvdc code

        print('Defaulting to first pvdc in the system viz.' +
              pvdc_refs[0].get('name'))
        cls._pvdc_href = pvdc_refs[0].get('href')
        cls._pvdc_name = pvdc_refs[0].get('name')

    @classmethod
    def create_org(cls):
        cls._basic_check()
        system = System(cls._sys_admin_client,
                        admin_resource=cls._sys_admin_client.get_admin())
        org_name = cls._config['vcd']['default_org_name']
        org_list = cls._sys_admin_client.get_org_list()
        for org in [o for o in org_list.Org if hasattr(org_list, 'Org')]:
            if org.get('name').lower() == org_name.lower():
                print('Reusing existing org ' + org_name + '.')
                cls._org_href = org.get('href')
                print('Using ' + cls._org_href)
                return
        print('Creating new org ' + org_name)
        result = system.create_org(org_name=org_name,
                                   full_org_name=org_name,
                                   is_enabled=True)
        cls._org_href = result.get('href')
        print('Created ' + cls._org_href)
        org_list = cls._sys_admin_client.get_org_list()
        for org in [o for o in org_list.Org if hasattr(org_list, 'Org')]:
            if org.get('name').lower() == org_name.lower():
                cls._org_href = org.get('href')
        print('Using ' + cls._org_href)

    @classmethod
    def create_users(cls):
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        org = Org(cls._sys_admin_client, href=cls._org_href)
        for role_enum in cls._user_name_for_roles.keys():
            user_name = cls._user_name_for_roles[role_enum]
            user_records = org.list_users(name_filter=('name', user_name))
            if len(list(user_records)) > 0:
                print('Reusing existing user ' + user_name + '.')
                continue
            role = org.get_role_record(role_enum.value)
            print('Creating user ' + user_name + '.')
            org.create_user(
                user_name=user_name,
                password=cls._config['vcd']['default_org_user_password'],
                role_href=role.get('href'),
                is_enabled=True)

    @classmethod
    def create_ovdc(cls):
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        org = Org(cls._sys_admin_client, href=cls._org_href)
        ovdc_name = cls._config['vcd']['default_ovdc_name']
        for vdc in org.list_vdcs():
            if vdc.get('name') == ovdc_name:
                print('Reusing existing ovdc ' + ovdc_name + '.')
                cls._ovdc_href = vdc.get('href')
                print('Using ' + cls._ovdc_href)
                return

        storage_profiles = [{
            'name': cls._config['vcd']['default_storage_profile_name'],
            'enabled': True,
            'units': 'MB',
            'limit': 0,
            'default': True
        }]

        system = System(cls._sys_admin_client,
                        admin_resource=cls._sys_admin_client.get_admin())
        netpools = system.list_network_pools()
        netpool_to_use = None
        netpool_name = cls._config['vcd']['default_netpool_name']
        if netpool_name is not '*':
            for item in netpools:
                if item.get('name') == netpool_name:
                    netpool_to_use = item.get('name')
                    break

        if netpool_to_use is None:
            print('Using first netpool in system viz. ' +
                  netpools[0].get('name'))
            netpool_to_use = netpools[0].get('name')

        print('Creating ovdc ' + ovdc_name + '.')
        vdc_resource = org.create_org_vdc(
            ovdc_name,
            cls._pvdc_name,
            network_pool_name=netpool_to_use,
            storage_profiles=storage_profiles,
            uses_fast_provisioning=True,
            is_thin_provision=True)

        cls._sys_admin_client.get_task_monitor().wait_for_success(
            task=vdc_resource.Tasks.Task[0])

        cls._ovdc_href = vdc_resource.get('href')
        print('Created ' + cls._ovdc_href)
        org.reload()
        for vdc in org.list_vdcs():
            if vdc.get('name') == ovdc_name:
                cls._ovdc_href = vdc.get('href')
        print('Using ' + cls._ovdc_href)

    @classmethod
    def create_catalog(cls):
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        catalog_author_client = Environment.get_client(
            CommonRoles.CATALOG_AUTHOR)
        org = Org(catalog_author_client, href=cls._org_href)
        catalog_name = cls._config['vcd']['default_catalog_name']
        catalog_records = org.list_catalogs()
        for catalog_record in catalog_records:
            if catalog_record.get('name') == catalog_name:
                print('Reusing existing catalog ' + catalog_name)
                catalog_author_client.logout()
                return

        print('Creating new catalog ' + catalog_name)
        catalog_resource = org.create_catalog(name=catalog_name,
                                              description='')
        catalog_author_client.get_task_monitor().wait_for_success(
            task=catalog_resource.Tasks.Task[0])
        catalog_author_client.logout()

    @classmethod
    def share_catalog(cls):
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        org = Org(cls._sys_admin_client, href=cls._org_href)
        catalog_name = cls._config['vcd']['default_catalog_name']
        catalog_records = org.list_catalogs()
        for catalog_record in catalog_records:
            if catalog_record.get('name') == catalog_name:
                print('Sharing catalog ' + catalog_name)
                org.share_catalog(name=catalog_name)
                return

        raise Exception('Catalog ' + catalog_name + 'doesn\'t exists.')

    @classmethod
    def upload_template(cls):
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        catalog_author_client = Environment.get_client(
            CommonRoles.CATALOG_AUTHOR)
        org = Org(catalog_author_client, href=cls._org_href)

        catalog_name = cls._config['vcd']['default_catalog_name']
        catalog_items = org.list_catalog_items(catalog_name)
        template_name = cls._config['vcd']['default_template_file_name']
        for item in catalog_items:
            if item.get('name') == template_name:
                print('Reusing existing template ' + template_name)
                catalog_author_client.logout()
                return

        print('Uploading template ' + template_name + ' to catalog ' +
              catalog_name + '.')
        org.upload_ovf(catalog_name=catalog_name, file_name=template_name)

        catalog_item = org.get_catalog_item(name=catalog_name,
                                            item_name=template_name)
        template = catalog_author_client.get_resource(
            catalog_item.Entity.get('href'))
        catalog_author_client.get_task_monitor().wait_for_success(
            task=template.Tasks.Task[0])
        catalog_author_client.logout()

    @classmethod
    def instantiate_vapp(cls):
        cls._basic_check()
        if cls._ovdc_href is None:
            raise Exception('OVDC ' + cls._config['vcd']['default_ovdc_name'] +
                            ' doesn\'t exist.')
        catalog_author_client = Environment.get_client(
            CommonRoles.CATALOG_AUTHOR)
        vdc = VDC(catalog_author_client, href=cls._ovdc_href)
        vapp_name = cls._config['vcd']['default_vapp_name']
        try:
            vdc.get_vapp(vapp_name)
        except Exception as e:
            if 'not found' in str(e):
                print('Instantiating vApp ' + vapp_name + '.')
                vapp_resource = vdc.instantiate_vapp(
                    name=vapp_name,
                    catalog=cls._config['vcd']['default_catalog_name'],
                    template=cls._config['vcd']['default_template_file_name'],
                    accept_all_eulas=True)
                catalog_author_client.get_task_monitor()\
                    .wait_for_success(task=vapp_resource.Tasks.Task[0])
                return
        finally:
            catalog_author_client.logout()
        print('Reusing existing vApp ' + vapp_name + '.')

    @classmethod
    def cleanup(cls):
        if cls._sys_admin_client is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning) # NOQA
                cls._sys_admin_client.logout()
                cls._sys_admin_client = None
                cls._pvdc_href = None
                cls._pvdc_name = None
                cls._org_href = None
                cls._ovdc_href = None

    @classmethod
    def get_default_org(cls, client):
        return Org(client, href=cls._org_href)

    @classmethod
    def get_default_vdc(cls, client):
        return VDC(client, href=cls._ovdc_href)

    @classmethod
    def get_default_username_for_role(cls, role_name):
        return cls._user_name_for_roles[role_name]

    @classmethod
    def get_default_vapp(cls, client):
        vdc = cls.get_default_vdc(client)
        vapp_name = cls._config['vcd']['default_vapp_name']
        vapp_resource = vdc.get_vapp(vapp_name)
        return VApp(client, resource=vapp_resource)

    @classmethod
    def get_default_vm_name(cls):
        return cls._config['vcd']['default_vm_name']
