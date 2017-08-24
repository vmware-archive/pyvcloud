from __future__ import print_function

from testconfig import config

from pyvcloud.vcloudair import VCA


class TestVCA:
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
        """Get Service Groups"""
        service_groups = self.vca.get_service_groups()
        assert service_groups
        assert len(service_groups) >= 0

    def test_0003(self):
        """Get Plans"""
        plans = self.vca.get_plans()
        assert plans
        assert len(plans) >= 0

    def test_0004(self):
        """Get Instances"""
        instances = self.vca.get_instances()
        assert instances
        assert len(instances) >= 0

    def test_0005(self):
        """Get Users"""
        users = self.vca.get_users()
        assert users
        assert len(users) >= 0
