import unittest

from pyvcloud.vcd.system import System
from pyvcloud.vcd.test import TestCase

class TestPVDC(TestCase):
    def test_create_pvdc(self):
        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)

        moRefs = system.create_provider_vdc(
            vimServerName=self.config['vcd']['vimServerName'],
            resourcePoolNames=self.config['vcd']['resourcePoolNames'],
            storageProfile=self.config['vcd']['storageProfile'],
            pvdcName=self.config['vcd']['pvdcName'],
            isEnabled=self.config['vcd']['isEnabled'],
            description=self.config['vcd']['description'])
        print(moRefs)

if __name__ == '__main__':
    unittest.main()