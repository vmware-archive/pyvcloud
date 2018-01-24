import unittest

from pyvcloud.vcd.system import System
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.utils import stdout_xml

class TestPVDC(TestCase):
    def test_create_pvdc(self):
        platform = Platform(self.client)

        pvdc = platform.create_provider_vdc(
            vimServerName=self.config['vcd']['vimServerName'],
            resourcePoolNames=self.config['vcd']['resourcePoolNames'],
            storageProfiles=self.config['vcd']['storageProfiles'],
            pvdcName=self.config['vcd']['pvdcName'],
            isEnabled=self.config['vcd']['isEnabled'],
            description=self.config['vcd']['description'])
        stdout_xml(pvdc)
        assert self.config['vcd']['pvdcName'] == pvdc.get('name')
        
if __name__ == '__main__':
    unittest.main()