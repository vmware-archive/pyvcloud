import random
import string
import unittest

from pyvcloud.vcd.system import System
from pyvcloud.vcd.test import TestCase


class TestSystem(TestCase):
    def test_create_org(self):
        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)
        org_name = "orgName".join(
            random.sample(string.ascii_lowercase, 4))
        org = system.create_org(org_name, "orgFullName")
        assert org.get('name') == org_name


if __name__ == '__main__':
    unittest.main()
