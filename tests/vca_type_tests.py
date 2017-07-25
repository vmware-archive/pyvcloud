from pyvcloud.vcloudair import VCA


class TestVCAType:
    def test_0001(self):
        """Identify vCloud Director Standalone"""
        vca = VCA(host='https://p1v21-vcd.vchs.vmware.com',
                  username='', verify=True, log=True)
        assert vca is not None
        service_type = vca.get_service_type()
        assert service_type == VCA.VCA_SERVICE_TYPE_STANDALONE

    def test_0002(self):
        """Identify vchs is not vCloud Director Standalone"""
        vca = VCA(
            host='https://vchs.vmware.com',
            username='',
            verify=True,
            log=True)
        assert vca is not None
        service_type = vca.get_service_type()
        assert service_type != VCA.VCA_SERVICE_TYPE_STANDALONE

    def test_0003(self):
        """Identify vca is not vCloud Director Standalone"""
        vca = VCA(
            host='https://vca.vmware.com',
            username='',
            verify=True,
            log=True)
        assert vca is not None
        service_type = vca.get_service_type()
        assert service_type != VCA.VCA_SERVICE_TYPE_STANDALONE

    def test_0011(self):
        """Identify vCloud Air vchs"""
        vca = VCA(
            host='https://vchs.vmware.com',
            username='',
            verify=True,
            log=True)
        assert vca is not None
        service_type = vca.get_service_type()
        assert service_type == VCA.VCA_SERVICE_TYPE_VCHS

    def test_0012(self):
        """Identify vca is not vCloud Air vchs"""
        vca = VCA(
            host='https://vca.vmware.com',
            username='',
            verify=True,
            log=True)
        assert vca is not None
        service_type = vca.get_service_type()
        assert service_type != VCA.VCA_SERVICE_TYPE_VCHS

    def test_0013(self):
        """Identify standalone is not vCloud Air vchs"""
        vca = VCA(host='https://p1v21-vcd.vchs.vmware.com',
                  username='', verify=True, log=True)
        assert vca is not None
        service_type = vca.get_service_type()
        assert service_type != VCA.VCA_SERVICE_TYPE_VCHS

    def test_0021(self):
        """Identify vCloud Air vca"""
        vca = VCA(host='https://iam.vchs.vmware.com',
                  username='', verify=True, log=True)
        assert vca is not None
        service_type = vca.get_service_type()
        assert service_type == VCA.VCA_SERVICE_TYPE_VCA

    def test_0022(self):
        """Identify vchs is not vCloud Air vca"""
        vca = VCA(
            host='https://vchs.vmware.com',
            username='',
            verify=True,
            log=True)
        assert vca is not None
        service_type = vca.get_service_type()
        assert service_type != VCA.VCA_SERVICE_TYPE_VCA

    def test_0023(self):
        """Identify standalone is not vCloud Air vca"""
        vca = VCA(host='https://p1v21-vcd.vchs.vmware.com',
                  username='', verify=True, log=True)
        assert vca is not None
        service_type = vca.get_service_type()
        assert service_type != VCA.VCA_SERVICE_TYPE_VCA
