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
    """Decorater function to skip execution of decorated function. To be used
        on test teardown methods.

    :param function: (function): The decorated function.

    :return: A function that either executes the decorated function or skips
        it, based on the value of a particular param in the environment
        configuration.
    """
    def wrapper(self):
        if not Environment._config['global']['developer_mode']:
            function(self)
        else:
            print('Skipping ' + function.__name__ +
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
    _sys_admin_client = None
    _pvdc_href = None
    _pvdc_name = None
    _org_href = None
    _ovdc_href = None
    _vapp_href = None

    _user_name_for_roles = {
        CommonRoles.CATALOG_AUTHOR: 'catalog_author',
        CommonRoles.CONSOLE_ACCESS_ONLY: 'console_user',
        CommonRoles.ORGANIZATION_ADMINISTRATOR: 'org_admin',
        CommonRoles.VAPP_AUTHOR: 'vapp_author',
        CommonRoles.VAPP_USER: 'vapp_user'}

    @classmethod
    def init(cls, config_data):
        """Initializer for Environment class.

        :param config_data: (PyYAML object): A PyYAML object that contains the
            yaml representation of configuration data read from the config
            file.

        :return: Nothing
        """
        cls._config = config_data
        if not cls._config['connection']['verify'] and \
           cls._config['connection']['disable_ssl_warnings']:
            requests.packages.urllib3.disable_warnings()

    @classmethod
    def _basic_check(cls):
        """Does basic sanity check for configuration and sys admin client.

        :return: Nothing

        :raises: Exception: If the basic configuration is missing.
        """
        if cls._config is None:
            raise Exception('Missing base configuration.')
        if cls._sys_admin_client is None:
            cls.get_sys_admin_client()

    @classmethod
    def get_sys_admin_client(cls):
        """Returns the sys admin client, creates one if required.

        :return: A :class: pyvcloud.vcd.client.Client object representing
            the sys admin client.

        :raises: Exception: If the basic configuration is missing.
        """
        if cls._config is None:
            raise Exception('Missing base configuration.')

        if cls._sys_admin_client is None:
            org = cls._config['vcd']['sys_org_name']
            password = cls._config['vcd']['sys_admin_pass']
            username = cls._config['vcd']['sys_admin_username']
            cls._sys_admin_client = cls.get_client(org=org,
                                                   username=username,
                                                   password=password)

        return cls._sys_admin_client

    @classmethod
    def get_client_in_default_org(cls, role):
        """Returns a client for a user with the specified role in the default
           test org.

           :param role: (CommonRoles) : The role of the user.

           :return: A :class: pyvcloud.vcd.client.Client object.

           :raises: Exception: If the basic configuration is missing.
        """
        if cls._config is None:
            raise Exception('Missing base configuration.')

        org = cls._config['vcd']['default_org_name']
        username = cls._user_name_for_roles[role]
        password = cls._config['vcd']['default_org_user_password']

        return cls.get_client(org=org, username=username, password=password)

    @classmethod
    def get_client(cls, org, username, password):
        """Returns a client for a user with the specified username-password
            combo in a given org.

        :param org: (str) : The name of the organization, which the user
            belongs to.
        :param username: (str) : The username of the user.
        :param password: (str) :  The password of the user.

        :return: A :class: pyvcloud.vcd.client.Client object.

        :raises: Exception: If the basic configuration is missing.
        """
        if cls._config is None:
            raise Exception('Missing base configuration.')

        client = Client(
            cls._config['vcd']['host'],
            api_version=cls._config['vcd']['api_version'],
            verify_ssl_certs=cls._config['connection']['verify'],
            log_file=cls._config['logging']['default_log_filename'],
            log_requests=cls._config['logging']['log_requests'],
            log_headers=cls._config['logging']['log_headers'],
            log_bodies=cls._config['logging']['log_bodies'])

        client.set_credentials(BasicLoginCredentials(username, org, password))

        return client

    @classmethod
    def attach_vc(cls):
        """Attaches VC and NSX to vCD as per config file, if VC is already
            attached no further action is taken.

        :return: Nothing
        """
        cls._basic_check()
        platform = Platform(cls._sys_admin_client)
        vc_name = cls._config['vc']['vcenter_host_name']
        for record in platform.list_vcenters():
            if record.get('name').lower() == vc_name.lower():
                print(vc_name + ' is already attached.')
                return
        # Untested code - see VCDA-603
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
        # TODO wait for async task to finish

    @classmethod
    def create_pvdc(cls):
        """Creates a pvdc by the name specified in the config file, skips
            creating one, if such a pvdc already exists. Also stores the
            href and name of the pvdc as class variables for future use.

        :return: Nothing
        """
        cls._basic_check()
        pvdc_name = cls._config['vcd']['default_pvdc_name']

        system = System(cls._sys_admin_client,
                        admin_resource=cls._sys_admin_client.get_admin())

        pvdc_refs = system.list_provider_vdcs()
        if pvdc_name is not '*':
            for pvdc_ref in pvdc_refs:
                if pvdc_ref.get('name').lower() == pvdc_name.lower():
                    print('Reusing existing ' + pvdc_name)
                    cls._pvdc_href = pvdc_ref.get('href')
                    cls._pvdc_name = pvdc_name
                    return
            print('Creating new pvdc' + pvdc_name)
            # TODO : use create pvdc code - see VCDA-603

        print('Defaulting to first pvdc in the system viz.' +
              pvdc_refs[0].get('name'))
        cls._pvdc_href = pvdc_refs[0].get('href')
        cls._pvdc_name = pvdc_refs[0].get('name')

    @classmethod
    def create_org(cls):
        """Creates an org by the name specified in the config file, skips
            creating one, if such an org already exists. Also stores the href
            of the org as class variable for future use.

        :return: Nothing
        """
        cls._basic_check()
        system = System(cls._sys_admin_client,
                        admin_resource=cls._sys_admin_client.get_admin())
        org_name = cls._config['vcd']['default_org_name']
        org_list = cls._sys_admin_client.get_org_list()
        for org in [o for o in org_list.Org if hasattr(org_list, 'Org')]:
            if org.get('name').lower() == org_name.lower():
                print('Reusing existing org ' + org_name + '.')
                cls._org_href = org.get('href')
                return
        print('Creating new org ' + org_name)
        system.create_org(org_name=org_name,
                          full_org_name=org_name,
                          is_enabled=True)
        # The following contraption is required to get the non admin href of
        # the org. The result of create_org() contains the admin version of
        # the href, since we created the org as a sys admin.
        org_list = cls._sys_admin_client.get_org_list()
        for org in [o for o in org_list.Org if hasattr(org_list, 'Org')]:
            if org.get('name').lower() == org_name.lower():
                cls._org_href = org.get('href')

    @classmethod
    def create_users(cls):
        """Creates users for each of the roles in CommonRoles, skips creating
            users which are already present in the org.

        :return: Nothing

        :raises: Exception: If the class variable _org_href is not populated.
        """
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
        """Creates an orgvdc by the name specified in the config file, skips
            creating one, if such an orgvdc already exists. Also stores the
            href of the orgvdc as class variable for future use.

        :return: Nothing

        :raises: Exception: If the class variable _org_href or _pvdc_name
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
                print('Reusing existing ovdc ' + ovdc_name + '.')
                cls._ovdc_href = vdc.get('href')
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
        netpool_to_use = cls._get_netpool_name_to_use(system)

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

        org.reload()
        # The following contraption is required to get the non admin href of
        # the ovdc. vdc_resource contains the admin version of the href since
        # we created the ovdc as a sys admin.
        for vdc in org.list_vdcs():
            if vdc.get('name').lower() == ovdc_name.lower():
                cls._ovdc_href = vdc.get('href')

    @classmethod
    def _get_netpool_name_to_use(cls, system):
        """ Determines the name of the netpool that will be used for the
            orgVDC. Defaults to the first netpool in the system.

        :param system: A :class: pyvcloud.vcd.system.System object

        :return: (str): Name of the netpool to use
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
            print('Using first netpool in system viz. ' +
                  netpools[0].get('name'))
            netpool_to_use = netpools[0].get('name')

        return netpool_to_use

    @classmethod
    def create_catalog(cls):
        """Creates a catalog by the name specified in the config file, skips
            creating one, if such a catalog already exists.

        :return: Nothing

        :raises: Exception: If the class variable _org_href is not populated.
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
                    print('Reusing existing catalog ' + catalog_name)
                    return

            print('Creating new catalog ' + catalog_name)
            catalog_resource = org.create_catalog(name=catalog_name,
                                                  description='')
            catalog_author_client.get_task_monitor().wait_for_success(
                task=catalog_resource.Tasks.Task[0])
        finally:
            catalog_author_client.logout()

    @classmethod
    def share_catalog(cls):
        """Shares the test catalog with all members in the test org.

        :return: Nothing

        :raises: Exception: If the class variable _org_href is not populated
            or the catalog in question is missing.
        """
        cls._basic_check()
        if cls._org_href is None:
            raise Exception('Org ' + cls._config['vcd']['default_org_name'] +
                            ' doesn\'t exist.')

        org = Org(cls._sys_admin_client, href=cls._org_href)
        catalog_name = cls._config['vcd']['default_catalog_name']
        catalog_records = org.list_catalogs()
        for catalog_record in catalog_records:
            if catalog_record.get('name').lower() == catalog_name.lower():
                print('Sharing catalog ' + catalog_name)
                # TODO : This method is buggy, share_catalog shares with only
                # org-admins of other orgs - see VCDA-603
                org.share_catalog(name=catalog_name)
                return

        raise Exception('Catalog ' + catalog_name + 'doesn\'t exists.')

    @classmethod
    def upload_template(cls):
        """Uploads the test template to the test catalog. If template
            already exists in the catalog then skips uploading it.

        :return: Nothing

        :raises: Exception: If the class variable _org_href is not populated.
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
                    print('Reusing existing template ' + template_name)
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
        finally:
            catalog_author_client.logout()

    @classmethod
    def instantiate_vapp(cls):
        """Instantiates the test template in the test catalog to create the
            test vApp. If the vApp already exists then skips creating it.

        :return: Nothing

        :raises: Exception: If the class variable _ovdc_href is not populated.
        """
        cls._basic_check()
        if cls._ovdc_href is None:
            raise Exception('OVDC ' + cls._config['vcd']['default_ovdc_name'] +
                            ' doesn\'t exist.')

        try:
            # TODO : use vApp author - see VCDA-603
            catalog_author_client = Environment.get_client_in_default_org(
                CommonRoles.CATALOG_AUTHOR)
            vdc = VDC(catalog_author_client, href=cls._ovdc_href)
            vapp_name = cls._config['vcd']['default_vapp_name']
            vapp_resource = vdc.get_vapp(vapp_name)
            print('Reusing existing vApp ' + vapp_name + '.')
            cls._vapp_href = vapp_resource.get('href')
            # TODO : Change to ResourceNotFoundException -- see VCDA-603
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
                cls._vapp_href = vapp_resource.get('href')
        finally:
            catalog_author_client.logout()

    @classmethod
    def cleanup(cls):
        """Cleans up the various class variables.

        :return: Nothing
        """
        if cls._sys_admin_client is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning) # NOQA
                cls._sys_admin_client.logout()
                cls._sys_admin_client = None
                cls._pvdc_href = None
                cls._pvdc_name = None
                cls._org_href = None
                cls._ovdc_href = None
                cls._vapp_href = None

    @classmethod
    def get_test_org(cls, client):
        """Gets the org used for testing

        :return: A :class: pyvcloud.vcd.org.Org object representing the
            org in which all tests will run.
        """
        return Org(client, href=cls._org_href)

    @classmethod
    def get_test_vdc(cls, client):
        """Gets the vdc for testing

        :return: A :class: pyvcloud.vcd.vdc.VDC object representing the
            vdc that is backing the org in which all tests will run.
        """
        return VDC(client, href=cls._ovdc_href)

    @classmethod
    def get_username_for_role_in_test_org(cls, role_name):
        """Gets the username of the user in the test org who has a
            particular role.

        :param role_name: (str): Name of the role which the concerned
            user has.

        :return (str): The username of the concerned user
        """
        return cls._user_name_for_roles[role_name]

    @classmethod
    def get_default_vapp(cls, client):
        """Gets the default vapp that will be used for testing.

        :return: A :class: pyvcloud.vcd.vapp.VApp object representing the
            vApp that will be used in tests.
        """
        return VApp(client, href=cls._vapp_href)

    @classmethod
    def get_default_vm_name(cls):
        """Get the name of the default vm that will be used for testing.

        :return (str): The name of the test vm.
        """
        return cls._config['vcd']['default_vm_name']
