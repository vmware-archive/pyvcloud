from nose.tools import with_setup
from testconfig import config
from pyvcloud.vcloudair import VCA
from pyvcloud.schema.vcd.v1_5.schemas.vcloud.networkType import NatRuleType, GatewayNatRuleType, ReferenceType, NatServiceType, FirewallRuleType, ProtocolsType


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
        self.vca = VCA(host=host, username=username, service_type=service_type, version=version, verify=True, log=True)
        assert self.vca
        if 'vcd' == service_type:
            result = self.vca.login(password=password, org=org)
            assert result
            result = self.vca.login(token=self.vca.token, org=org, org_url=self.vca.vcloud_session.org_url)
            assert result
        elif 'subscription' == service_type:    
            result = self.vca.login(password=password)
            assert result
        elif vcloudair.VCA_SERVICE_TYPE_ONDEMAND == service_type:    
            result = self.vca.login(password=password)
            assert result


    def logout_from_vcloud(self):
        """Logout from vCloud"""
        print 'logout'
        selfl.vca.logout()
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
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.create_vapp(vdc_name, vapp_name, template, catalog, vm_name=vm_name)
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
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.me.get_status() == 8


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
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(lambda n: n.name == network, self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.connect_to_network(nets[0].name, nets[0].href)
        result = self.vca.block_until_completed(task)
        assert result


    def test_0014(self):
        """Connect VM to network"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(lambda n: n.name == network, self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.connect_vms(nets[0].name, connection_index=0, ip_allocation_mode=mode.upper())
        result = self.vca.block_until_completed(task)
        assert result


    def test_0018(self):
        """Validate vApp State is powered off (8)"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.me.get_status() == 8


    def test_0020(self):
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
        assert the_vapp != None
        assert the_vapp.me.get_status() == 4


    def test_0022(self):
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
        assert the_vapp != None
        assert the_vapp.me.get_status() == 8


    def test_0099(self):
        """Delete vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.delete_vapp(vdc_name, vapp_name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp == None


