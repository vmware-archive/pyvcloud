from nose.tools import with_setup
from testconfig import config
from pyvcloud import vcloudair
from pyvcloud.vcloudair import VCA
from pyvcloud.sqlair import SQLAir


class TestSQLAir:

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
        if vcloudair.VCA_SERVICE_TYPE_STANDALONE == service_type:
            result = self.vca.login(password=password, org=org)
            assert result
            result = self.vca.login(
                token=self.vca.token,
                org=org,
                org_url=self.vca.vcloud_session.org_url)
            assert result
        elif vcloudair.VCA_SERVICE_TYPE_SUBSCRIPTION == service_type:
            result = self.vca.login(password=password)
            assert result
            result = self.vca.login(token=self.vca.token)
            assert result
            result = self.vca.login_to_org(service, org)
            assert result
        elif vcloudair.VCA_SERVICE_TYPE_ONDEMAND == service_type:
            result = self.vca.login(password=password)
            assert result
            # result = self.vca.login_to_instance(password=password, instance=instance, token=None, org_url=None)
            # assert result
            # result = self.vca.login_to_instance(password=None, instance=instance, token=self.vca.vcloud_session.token, org_url=self.vca.vcloud_session.org_url)
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
        """Check SQLAir access"""
        # vdc_name = config['vcloud']['vdc']
        # the_vdc = self.vca.get_vdc(vdc_name)
        # assert the_vdc
        # assert the_vdc.get_name() == vdc_name
        sql_air = SQLAir(
            token=self.vca.token,
            version='5.7',
            verify=True,
            log=True)
        response_code = sql_air.ping()
        assert response_code == 200

    def test_0003(self):
        """Get MSSQL Service Info"""
        sql_air = SQLAir(
            token=self.vca.token,
            version='5.7',
            verify=True,
            log=True)
        service_code = 'mssql'
        service_mssql = sql_air.get_service(service_code)
        assert service_mssql
        assert service_mssql['serviceCode'] == service_code

    def test_0003(self):
        """Get DB Instances"""
        sql_air = SQLAir(
            token=self.vca.token,
            version='5.7',
            verify=True,
            log=True)
        service_code = 'mssql'
        instances = sql_air.get_instances(service_code)
        assert instances
        assert instances['total'] >= 0

    # def test_0004(self):
    #     """Get DB Instance"""
    #     sql_air = SQLAir(token=self.vca.token, version='5.7', verify=True, log=True)
    #     sql_air.get_instance('e319bcc6-b4d9-45be-8d2e-f90676410f3a')
