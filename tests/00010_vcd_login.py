from __future__ import print_function
from testconfig import config

from pyvcloud.vcloudair import VCA


class TestVDC:
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
        self.vca = VCA(host=host,
                       username=username,
                       service_type=service_type,
                       version=version,
                       verify=config['vcloud']['verify'],
                       log=True)
        assert self.vca
        result = self.vca.login(password=password, org=org)
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
