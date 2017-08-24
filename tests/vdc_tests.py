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
        instance = config['vcloud']['instance']
        self.vca = VCA(
            host=host,
            username=username,
            service_type=service_type,
            version=version,
            verify=True,
            log=True)
        assert self.vca
        if self.vca.VCA_SERVICE_TYPE_STANDALONE == service_type:
            raise Exception('not-supported')
        elif self.vca.VCA_SERVICE_TYPE_VCHS == service_type:
            raise Exception('not-supported')
        elif self.vca.VCA_SERVICE_TYPE_VCA == service_type:
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
        """Get VDC Templates"""
        templates = self.vca.get_vdc_templates()
