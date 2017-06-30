from nose.tools import with_setup
from testconfig import config
from pyvcloud import vcloudair
from pyvcloud.vcloudair import VCA
from pyvcloud.system import System
from os import environ
from xml.etree import ElementTree as ET

class TestExtensions:

    def __init__(self):
        self.vca = None
        self.login_to_vcloud()

    def login_to_vcloud(self):
        """Login to vCloud"""
        username = environ['VCLOUD_USERNAME']
        password = environ['VCLOUD_PASSWORD']
        service_type = VCA.VCA_SERVICE_TYPE_STANDALONE
        host = config['vcloud']['host']
        version = config['vcloud']['version']
        verify = config['vcloud']['verify']
        org = config['vcloud']['org']
        self.vca = VCA(host=host, username=username, service_type=service_type, version=version, verify=verify, log=True)
        assert self.vca
        result = self.vca.login(password=password, org=org)
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
        """List extensions"""
        system = System(session=self.vca.vcloud_session, verify=self.vca.verify, log=self.vca.log)
        extensions = system.get_extensions()
        assert extensions

    def test_0003(self):
        """Register extension"""
        name = config['vcloud']['ext_name']
        system = System(session=self.vca.vcloud_session, verify=self.vca.verify, log=self.vca.log)
        extension = system.register_extension(name, name, name, name)
        assert extension is not None
        assert name == extension.attrib['name']

    def test_0004(self):
        """Get extension"""
        system = System(session=self.vca.vcloud_session, verify=self.vca.verify, log=self.vca.log)
        extension = system.get_extension(config['vcloud']['ext_name'])
        assert extension is not None
        name = extension.attrib['name']
        assert name == config['vcloud']['ext_name']

    def test_0005(self):
        """Enable extension"""
        system = System(session=self.vca.vcloud_session, verify=self.vca.verify, log=self.vca.log)
        extension = system.get_extension(config['vcloud']['ext_name'])
        assert extension is not None
        name = extension.attrib['name']
        assert name == config['vcloud']['ext_name']
        result = system.enable_extension(name,
                                         extension.attrib['href'],
                                         enabled=True)
        extension = system.get_extension(config['vcloud']['ext_name'])
        assert extension is not None
        name = extension.attrib['name']
        assert name == config['vcloud']['ext_name']
        enabled = '****'
        for node in extension.findall('.//{http://www.vmware.com/vcloud/extension/v1.5}Enabled'):
            enabled = node.text
        assert enabled == 'true'

    def test_0006(self):
        """Disable extension"""
        system = System(session=self.vca.vcloud_session, verify=self.vca.verify, log=self.vca.log)
        extension = system.get_extension(config['vcloud']['ext_name'])
        assert extension is not None
        name = extension.attrib['name']
        assert name == config['vcloud']['ext_name']
        result = system.enable_extension(name,
                                         extension.attrib['href'],
                                         enabled=False)
        extension = system.get_extension(config['vcloud']['ext_name'])
        assert extension is not None
        name = extension.attrib['name']
        assert name == config['vcloud']['ext_name']
        enabled = '****'
        for node in extension.findall('.//{http://www.vmware.com/vcloud/extension/v1.5}Enabled'):
            enabled = node.text
        assert enabled == 'false'

    def test_0007(self):
        """Unregister extension"""
        system = System(session=self.vca.vcloud_session, verify=self.vca.verify, log=self.vca.log)
        extension = system.get_extension(config['vcloud']['ext_name'])
        assert extension is not None
        name = extension.attrib['name']
        assert name == config['vcloud']['ext_name']
        result = system.unregister_extension(config['vcloud']['ext_name'], extension.attrib['href'])
        extension = system.get_extension(config['vcloud']['ext_name'])
        assert extension is None
