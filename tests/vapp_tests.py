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
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.create_vapp(
            vdc_name,
            vapp_name,
            template,
            catalog,
            network_name=network,
            vm_name=vm_name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vdc = self.vca.get_vdc(vdc_name)
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name

    def test_0005(self):
        """Validate vApp State is powered off (8)"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.me.get_status() == 8

    def test_0009(self):
        """Disconnect VM from pre-defined networks"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.disconnect_vms()
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        vm_info = the_vapp.get_vms_network_info()
        print(vm_info)
        assert vm_info
        assert len(vm_info) == 1
        assert len(vm_info[0]) == 0

    def test_0010(self):
        """Disconnect vApp from pre-defined networks"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.disconnect_from_networks()
        assert task
        result = self.vca.block_until_completed(task)
        assert result

    def test_0012(self):
        """Connect vApp to network"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.connect_to_network(nets[0].name, nets[0].href)
        result = self.vca.block_until_completed(task)
        assert result

    def test_0013(self):
        """Connect VM to network - MANUAL static IP mode"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        ip_address = config['vcloud']['ip_address']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.connect_vms(
            nets[0].name,
            connection_index=0,
            ip_allocation_mode='MANUAL',
            ip_address=ip_address)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        vm_info = the_vapp.get_vms_network_info()
        print (vm_info)
        assert vm_info
        assert len(vm_info) == 1
        assert len(vm_info[0]) == 1
        assert vm_info[0][0].get('network_name') == network
        assert vm_info[0][0].get('allocation_mode') == 'MANUAL'
        assert vm_info[0][0].get('ip') == ip_address

    def test_0014(self):
        """Disconnect VM from network"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.disconnect_vms(nets[0].name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        vm_info = the_vapp.get_vms_network_info()
        assert vm_info
        assert len(vm_info) == 1
        assert len(vm_info[0]) == 0

    def test_0015(self):
        """Connect VM to network - POOL mode"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.connect_vms(
            nets[0].name,
            connection_index=0,
            ip_allocation_mode='POOL')
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        vm_info = the_vapp.get_vms_network_info()
        print(vm_info)
        assert vm_info
        assert len(vm_info) == 1
        assert len(vm_info[0]) == 1
        assert vm_info[0][0].get('network_name') == network
        assert vm_info[0][0].get('allocation_mode') == 'POOL'

    def test_0016(self):
        """Disconnect VM from network"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.disconnect_vms(nets[0].name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        vm_info = the_vapp.get_vms_network_info()
        assert vm_info
        assert len(vm_info) == 1
        assert len(vm_info[0]) == 0

    def test_0017(self):
        """Connect VM to network - DHCP mode"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.connect_vms(
            nets[0].name,
            connection_index=0,
            ip_allocation_mode='DHCP')
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        vm_info = the_vapp.get_vms_network_info()
        print(vm_info)
        assert vm_info
        assert len(vm_info) == 1
        assert len(vm_info[0]) == 1
        assert vm_info[0][0].get('network_name') == network
        assert vm_info[0][0].get('allocation_mode') == 'DHCP'

    def test_0018(self):
        """Disconnect VM from network"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.disconnect_vms(nets[0].name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        vm_info = the_vapp.get_vms_network_info()
        assert vm_info
        assert len(vm_info) == 1
        assert len(vm_info[0]) == 0

    def test_0019(self):
        """Connect single VM to network - DHCP mode"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.connect_vm(
            vm_name,
            nets[0].name,
            connection_index=0,
            ip_allocation_mode='DHCP')
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        vm_info = the_vapp.get_vms_network_info()
        print(vm_info)
        assert vm_info
        assert len(vm_info) == 1
        assert len(vm_info[0]) == 1
        assert vm_info[0][0].get('network_name') == network
        assert vm_info[0][0].get('allocation_mode') == 'DHCP'

    def test_0020(self):
        """Disconnect VM from network"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.disconnect_vm(vm_name, nets[0].name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        vm_info = the_vapp.get_vms_network_info()
        assert vm_info
        assert len(vm_info) == 1
        assert len(vm_info[0]) == 0

    def test_0030(self):
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
