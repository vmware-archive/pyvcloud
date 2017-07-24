from __future__ import print_function
from __future__ import print_function

from testconfig import config

from pyvcloud.vcloudair import VCA


class TestNet:
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

    def test_0003(self):
        """Get Networks"""
        print('')
        vdc_name = config['vcloud']['vdc']
        networks = self.vca.get_networks(vdc_name)
        for network in networks:
            print(network)

    def test_0004(self):
        """ Connect to Networks"""
        print('')
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network_name = config['vcloud']['network']
        network_name2 = config['vcloud']['network2']
        network_name3 = config['vcloud']['network3']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name

        print('disconnect vms')
        task = the_vapp.disconnect_vms()
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        print('disconnect vapp')
        task = the_vapp.disconnect_from_networks()
        assert task
        result = self.vca.block_until_completed(task)
        assert result

        index = 0
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        nets = filter(lambda n: n.name == network_name,
                      self.vca.get_networks(vdc_name))
        mode = 'POOL'
        if len(nets) == 1:
            print("connecting vApp to network"
                  " '%s' with mode '%s'" %
                  (network_name, mode))
            task = the_vapp.connect_to_network(
                nets[0].name, nets[0].href)
            assert task
            result = self.vca.block_until_completed(task)
            assert result
            the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
            ip = None
            task = the_vapp.connect_vms(
                nets[0].name,
                connection_index=index,
                connections_primary_index=0,
                ip_allocation_mode=mode.upper(),
                mac_address=None, ip_address=ip)
            assert task
            result = self.vca.block_until_completed(task)
            assert result

        index = index + 1
        nets = filter(lambda n: n.name == network_name2,
                      self.vca.get_networks(vdc_name))
        mode = 'POOL'
        if len(nets) == 1:
            print("connecting vApp to network"
                  " '%s' with mode '%s'" %
                  (network_name2, mode))
            task = the_vapp.connect_to_network(
                nets[0].name, nets[0].href)
            assert task
            result = self.vca.block_until_completed(task)
            assert result
            the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
            ip = None
            task = the_vapp.connect_vms(
                nets[0].name,
                connection_index=index,
                connections_primary_index=0,
                ip_allocation_mode=mode.upper(),
                mac_address=None, ip_address=ip)
            assert task
            result = self.vca.block_until_completed(task)
            assert result

        index = index + 1
        nets = filter(lambda n: n.name == network_name3,
                      self.vca.get_networks(vdc_name))
        mode = 'POOL'
        if len(nets) == 1:
            print("connecting vApp to network"
                  " '%s' with mode '%s'" %
                  (network_name3, mode))
            task = the_vapp.connect_to_network(
                nets[0].name, nets[0].href)
            assert task
            result = self.vca.block_until_completed(task)
            assert result
            the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
            ip = None
            task = the_vapp.connect_vms(
                nets[0].name,
                connection_index=index,
                connections_primary_index=0,
                ip_allocation_mode=mode.upper(),
                mac_address=None, ip_address=ip)
            assert task
            result = self.vca.block_until_completed(task)
            assert result

        print('status=%s' % the_vapp.me.get_status())
        if (4 == the_vapp.me.get_status()):
            print('undeploy vApp')
            task = the_vapp.undeploy()
            if task is not None:
                result = self.vca.block_until_completed(task)

        print('set guest customization')
        task = the_vapp.customize_guest_os(vm_name)
        assert task
        result = self.vca.block_until_completed(task)
        print('force customization')
        task = the_vapp.force_customization(vm_name)
        print(task)
        if task is not None:
            result = self.vca.block_until_completed(task)
        task = the_vapp.deploy()
        if task is not None:
            result = self.vca.block_until_completed(task)
