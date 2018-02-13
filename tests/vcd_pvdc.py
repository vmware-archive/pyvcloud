import unittest

from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.test import TestCase


class TestPVDC(TestCase):
    def test_create_pvdc(self):
        platform = Platform(self.client)

        pvdc = platform.create_provider_vdc(
            vim_server_name=self.config['vcd']['vimServerName'],
            resource_pool_names=self.config['vcd']['resourcePoolNames'],
            storage_profiles=self.config['vcd']['storageProfiles'],
            pvdc_name=self.config['vcd']['pvdcName'],
            is_enabled=self.config['vcd']['isEnabled'],
            description=self.config['vcd']['description'],
            highest_supp_hw_vers=self.config['vcd']['highestSuppHWVers'],
            vxlan_network_pool=self.config['vcd']['vxlanNetworkPool'])
        assert self.config['vcd']['pvdcName'] == pvdc.get('name')


if __name__ == '__main__':
    unittest.main()
