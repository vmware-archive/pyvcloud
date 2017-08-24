from __future__ import print_function
from nose.tools import with_setup
from testconfig import config
from pyvcloud import vcloudair
from pyvcloud.vcloudair import VCA


class TestVCASSO:

    def __init__(self):
        self.vca = None
        self.instance = None
        self.login_to_vcloud()

    def login_to_vcloud(self):
        """Login to vCloud VCA"""
        username = config['vcloud']['username']
        password = config['vcloud']['password']
        host = config['vcloud']['host']
        version = config['vcloud']['version']
        self.instance = config['vcloud']['instance']
        self.vca = VCA(
            host=host,
            username=username,
            service_type='vca',
            version=version,
            verify=True,
            log=True)
        assert self.vca
        result = self.vca.login(password=password)
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

    def test_002(self):
        """Login to instance no password"""
        result = self.vca.login_to_instance_sso(instance=self.instance)
        assert result
        # org = self.vca.vcloud_session.org
