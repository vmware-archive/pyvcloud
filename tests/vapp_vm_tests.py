from __future__ import print_function

from testconfig import config

from pyvcloud.vcloudair import VCA


class TestVApp:
    def __init__(self):
        self.vca = None
        self.login_to_vcloud()

    def login_to_vcloud(self):
        """Login to vCloud"""
        username = config['vcloud']['username']
        password = config['vcloud']['password']
        service_type = config['vcloud']['service_type']
        host = config['vcloud']['host']
        version = config['vcloud']['version']
        org = config['vcloud']['org']
        service = config['vcloud']['service']
        instance = config['vcloud']['instance']
        self.vca = VCA(
            host=host,
            username=username,
            service_type=service_type,
            version=version,
            verify=True,
            log=True)
        assert self.vca
        if VCA.VCA_SERVICE_TYPE_STANDALONE == service_type:
            result = self.vca.login(password=password, org=org)
            assert result
            result = self.vca.login(
                token=self.vca.token,
                org=org,
                org_url=self.vca.vcloud_session.org_url)
            assert result
        elif VCA.VCA_SERVICE_TYPE_VCHS == service_type:
            result = self.vca.login(password=password)
            assert result
            result = self.vca.login(token=self.vca.token)
            assert result
            result = self.vca.login_to_org(service, org)
            assert result
        elif VCA.VCA_SERVICE_TYPE_VCA == service_type:
            result = self.vca.login(password=password)
            assert result
            result = self.vca.login_to_instance(
                password=password, instance=instance, token=None, org_url=None)
            assert result
            result = self.vca.login_to_instance(
                password=None,
                instance=instance,
                token=self.vca.vcloud_session.token,
                org_url=self.vca.vcloud_session.org_url)
            assert result

    def logout_from_vcloud(self):
        """Logout from vCloud"""
        print('logout')
        self.vca.logout()
        self.vca = None
        assert self.vca is None

    def test_0001(self):
        """Loggin in to vCloud"""
        assert self.vca.token

    def test_0002(self):
        """Get VDC"""
        vdc_name = config['vcloud']['vdc']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name

    def test_0003(self):
        """Create vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        cpu = config['vcloud']['cpus_new']
        memory = config['vcloud']['memory_new']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.create_vapp(vdc_name, vapp_name, template, catalog,
                                    vm_name=vm_name,
                                    vm_cpus=cpu,
                                    vm_memory=memory)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vdc = self.vca.get_vdc(vdc_name)
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name

    def test_0004(self):
        """Validate vApp State is powered off (8)"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.me.get_status() == 8

    def test_0031(self):
        """Power On vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        assert the_vapp.me.get_status() == 8
        task = the_vapp.poweron()
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp is not None
        assert the_vapp.me.get_status() == 4

    def test_0032(self):
        """Power Off vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        assert the_vapp.me.get_status() == 4
        task = the_vapp.poweroff()
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp is not None
        assert the_vapp.me.get_status() == 8

    def test_0099(self):
        """Delete vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.delete_vapp(vdc_name, vapp_name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp is None
