from nose.tools import with_setup
from testconfig import config
from pyvcloud.vcloudair import VCA

class TestVCloud:
    
    def __init__(self):
        self.vca = None
        self.login_to_vcloud()
 
    # def setup(self):
    #     print ("TestUM:setup() before each test method")
    #
    # def teardown(self):
    #     print ("TestUM:teardown() after each test method")
 
    # @classmethod
    # def setup_class(cls):
    #     print ("setup_class() before any methods in this class")
    #     login_to_vcloud()
    #
    # @classmethod
    # def teardown_class(cls):
    #     print ("teardown_class() after any methods in this class")
        
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
        elif 'ondemand' == service_type:    
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
        vdc = config['vcloud']['vdc']
        the_vdc = self.vca.get_vdc(vdc)        
        assert the_vdc
        assert the_vdc.get_name() == vdc
    
    def test_0003(self):
        """Create vApp"""
        vdc = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc)
        assert the_vdc
        assert the_vdc.get_name() == vdc
        task = self.vca.create_vapp(vdc, vapp_name, template, catalog, vm_name=vm_name)
        assert task
        self.vca.block_until_completed(task)
        the_vdc = self.vca.get_vdc(vdc)
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        
    def test_0004(self):
        """Change vApp/VM Memory"""
        vdc = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        memory = config['vcloud']['memory']
        memory_new = config['vcloud']['memory_new']
        the_vdc = self.vca.get_vdc(vdc)        
        assert the_vdc
        assert the_vdc.get_name() == vdc
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        details = the_vapp.get_vms_details()
        assert details[0].get('memory_mb') == memory

    def test_0005(self):
        """Delete vApp"""
        vdc = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc)
        assert the_vdc
        assert the_vdc.get_name() == vdc
        task = self.vca.delete_vapp(vdc, vapp_name)
        assert task
        self.vca.block_until_completed(task)
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp == None
        
        
