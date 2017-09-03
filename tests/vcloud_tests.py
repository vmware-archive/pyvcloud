from __future__ import print_function
from testconfig import config

from pyvcloud.schema.vcd.v1_5.schemas.vcloud.networkType import ProtocolsType
from pyvcloud.vcloudair import VCA


class TestVCloud:
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
        verify = config['vcloud']['verify']
        self.vca = VCA(host=host, username=username,
                       service_type=service_type, version=version,
                       verify=verify, log=True)
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

    def test_0002(self):
        """Get VDC"""
        vdc_name = config['vcloud']['vdc']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name

    def test_0003(self):
        """Create vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.create_vapp(
            vdc_name,
            vapp_name,
            template,
            catalog,
            vm_name=vm_name,
            network_name=network)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vdc = self.vca.get_vdc(vdc_name)
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name

    def test_0004(self):
        """Clone vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.clone_vapp(
            vdc_name,
            vapp_name,
            vdc_name,
            vapp_name +
            '_clone')
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vdc = self.vca.get_vdc(vdc_name)
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name + '_clone')
        assert the_vapp
        assert the_vapp.name == vapp_name + '_clone'

    def test_0005(self):
        """Disconnect vApp from pre-defined networks"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.disconnect_from_networks()
        assert task
        result = self.vca.block_until_completed(task)
        assert result

    def test_0006(self):
        """Connect vApp to network"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.connect_to_network(nets[0].name, nets[0].href)
        result = self.vca.block_until_completed(task)
        assert result

    def test_0007(self):
        """Connect VM to network"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        nets = filter(
            lambda n: n.name == network,
            self.vca.get_networks(vdc_name))
        assert len(nets) == 1
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        task = the_vapp.connect_vms(
            nets[0].name,
            connection_index=0,
            ip_allocation_mode=mode.upper())
        result = self.vca.block_until_completed(task)
        assert result

    def test_0008(self):
        """Change vApp/VM Memory"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        memory = config['vcloud']['memory']
        memory_new = config['vcloud']['memory_new']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        details = the_vapp.get_vms_details()
        assert details[0].get('memory_mb') == memory
        task = the_vapp.modify_vm_memory(vm_name, memory_new)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        details = the_vapp.get_vms_details()
        assert details[0].get('memory_mb') == memory_new

    def test_0009(self):
        """Change vApp/VM CPU"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        cpus = config['vcloud']['cpus']
        cpus_new = config['vcloud']['cpus_new']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        details = the_vapp.get_vms_details()
        assert details[0].get('cpus') == cpus
        task = the_vapp.modify_vm_cpu(vm_name, cpus_new)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        details = the_vapp.get_vms_details()
        assert details[0].get('cpus') == cpus_new

    def test_0010(self):
        """Add NAT rule"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        gateway_name = config['vcloud']['gateway']
        rule_type = config['vcloud']['nat_rule_type']
        original_ip = config['vcloud']['nat_original_ip']
        original_port = config['vcloud']['nat_original_port']
        translated_ip = config['vcloud']['nat_translated_ip']
        translated_port = config['vcloud']['nat_translated_port']
        protocol = config['vcloud']['nat_protocol']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        the_gateway.add_nat_rule(
            rule_type,
            original_ip,
            original_port,
            translated_ip,
            translated_port,
            protocol)
        task = the_gateway.save_services_configuration()
        assert task
        result = self.vca.block_until_completed(task)
        assert result

    def test_0011(self):
        """Get NAT rule"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        gateway_name = config['vcloud']['gateway']
        rule_type = config['vcloud']['nat_rule_type']
        original_ip = config['vcloud']['nat_original_ip']
        original_port = str(config['vcloud']['nat_original_port'])
        translated_ip = config['vcloud']['nat_translated_ip']
        translated_port = str(config['vcloud']['nat_translated_port'])
        protocol = config['vcloud']['nat_protocol']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        nat_rules = the_gateway.get_nat_rules()
        found_rule = False
        for natRule in nat_rules:
            ruleId = natRule.get_Id()
            if rule_type == natRule.get_RuleType():
                gatewayNatRule = natRule.get_GatewayNatRule()
                gateway_original_ip = gatewayNatRule.get_OriginalIp(
                ) if gatewayNatRule.get_OriginalIp() else 'any'
                gateway_original_port = gatewayNatRule.get_OriginalPort(
                ) if gatewayNatRule.get_OriginalPort() else 'any'
                gateway_translated_ip = gatewayNatRule.get_TranslatedIp(
                ) if gatewayNatRule.get_TranslatedIp() else 'any'
                gateway_translated_port = gatewayNatRule.get_TranslatedPort(
                ) if gatewayNatRule.get_TranslatedPort() else 'any'
                gateway_protocol = gatewayNatRule.get_Protocol(
                ) if gatewayNatRule.get_Protocol() else 'any'
                if original_ip == gateway_original_ip and \
                                original_port == gateway_original_port and \
                                translated_ip == gateway_translated_ip and \
                                translated_port == gateway_translated_port and \
                                protocol == gateway_protocol:
                    found_rule = True
        assert found_rule

    def test_0012(self):
        """Delete NAT rule"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        gateway_name = config['vcloud']['gateway']
        rule_type = config['vcloud']['nat_rule_type']
        original_ip = config['vcloud']['nat_original_ip']
        original_port = str(config['vcloud']['nat_original_port'])
        translated_ip = config['vcloud']['nat_translated_ip']
        translated_port = str(config['vcloud']['nat_translated_port'])
        protocol = config['vcloud']['nat_protocol']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        details = the_vapp.get_vms_details()
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        found_rule = the_gateway.del_nat_rule(
            rule_type,
            original_ip,
            original_port,
            translated_ip,
            translated_port,
            protocol)
        assert found_rule
        task = the_gateway.save_services_configuration()
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        nat_rules = the_gateway.get_nat_rules()
        found_rule = False
        for natRule in nat_rules:
            ruleId = natRule.get_Id()
            if rule_type == natRule.get_RuleType():
                gatewayNatRule = natRule.get_GatewayNatRule()
                gateway_original_ip = gatewayNatRule.get_OriginalIp(
                ) if gatewayNatRule.get_OriginalIp() else 'any'
                gateway_original_port = gatewayNatRule.get_OriginalPort(
                ) if gatewayNatRule.get_OriginalPort() else 'any'
                gateway_translated_ip = gatewayNatRule.get_TranslatedIp(
                ) if gatewayNatRule.get_TranslatedIp() else 'any'
                gateway_translated_port = gatewayNatRule.get_TranslatedPort(
                ) if gatewayNatRule.get_TranslatedPort() else 'any'
                gateway_protocol = gatewayNatRule.get_Protocol(
                ) if gatewayNatRule.get_Protocol() else 'any'
                if original_ip == gateway_original_ip and \
                                original_port == gateway_original_port and \
                                translated_ip == gateway_translated_ip and \
                                translated_port == gateway_translated_port and \
                                protocol == gateway_protocol:
                    found_rule = True
                    break
        assert found_rule == False

    def test_0013(self):
        """Enable Firewall service"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        gateway_name = config['vcloud']['gateway']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        the_gateway.enable_fw(True)
        task = the_gateway.save_services_configuration()
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        assert the_gateway.is_fw_enabled()

    def test_0014(self):
        """Add Firewall rule"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        gateway_name = config['vcloud']['gateway']
        is_enable = config['vcloud']['fw_is_enable']
        description = config['vcloud']['fw_description']
        policy = config['vcloud']['fw_policy']
        dest_ip = config['vcloud']['fw_dest_port']
        dest_port = config['vcloud']['fw_dest_ip']
        protocol = config['vcloud']['fw_protocol']
        source_ip = config['vcloud']['fw_source_ip']
        source_port = config['vcloud']['fw_source_port']
        enable_logging = config['vcloud']['fw_enable_logging']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        the_gateway.add_fw_rule(
            is_enable,
            description,
            policy,
            protocol,
            dest_port,
            dest_ip,
            source_port,
            source_ip,
            enable_logging)
        task = the_gateway.save_services_configuration()
        assert task
        result = self.vca.block_until_completed(task)
        assert result

    def _create_protocols_type(self, protocol):
        all_protocols = {"Tcp": None, "Udp": None, "Icmp": None, "Any": None}
        all_protocols[protocol] = True
        return ProtocolsType(**all_protocols)

    def test_0015(self):
        """Get Firewall rule"""

        def create_protocol_list(protocol):
            plist = []
            plist.append(protocol.get_Tcp())
            plist.append(protocol.get_Any())
            plist.append(protocol.get_Tcp())
            plist.append(protocol.get_Udp())
            plist.append(protocol.get_Icmp())
            plist.append(protocol.get_Other())
            return plist

        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        gateway_name = config['vcloud']['gateway']
        is_enable = config['vcloud']['fw_is_enable']
        description = config['vcloud']['fw_description']
        policy = config['vcloud']['fw_policy']
        dest_ip = config['vcloud']['fw_dest_port']
        dest_port = config['vcloud']['fw_dest_ip']
        protocol = config['vcloud']['fw_protocol']
        source_ip = config['vcloud']['fw_source_ip']
        source_port = config['vcloud']['fw_source_port']
        enable_logging = config['vcloud']['fw_enable_logging']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        rules = the_gateway.get_fw_rules()
        to_find_trait = (
            create_protocol_list(
                self._create_protocols_type(protocol)),
            dest_port,
            dest_ip,
            source_port,
            source_ip)
        rule_found = False
        for rule in rules:
            current_trait = (create_protocol_list(rule.get_Protocols()),
                             rule.get_DestinationPortRange(),
                             rule.get_DestinationIp(),
                             rule.get_SourcePortRange(),
                             rule.get_SourceIp())
            if current_trait == to_find_trait:
                rule_found = True
                break
        assert rule_found

    def test_0016(self):
        """Delete Firewall rule"""

        def create_protocol_list(protocol):
            plist = []
            plist.append(protocol.get_Tcp())
            plist.append(protocol.get_Any())
            plist.append(protocol.get_Tcp())
            plist.append(protocol.get_Udp())
            plist.append(protocol.get_Icmp())
            plist.append(protocol.get_Other())
            return plist

        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        gateway_name = config['vcloud']['gateway']
        is_enable = config['vcloud']['fw_is_enable']
        description = config['vcloud']['fw_description']
        policy = config['vcloud']['fw_policy']
        dest_ip = config['vcloud']['fw_dest_port']
        dest_port = config['vcloud']['fw_dest_ip']
        protocol = config['vcloud']['fw_protocol']
        source_ip = config['vcloud']['fw_source_ip']
        source_port = config['vcloud']['fw_source_port']
        enable_logging = config['vcloud']['fw_enable_logging']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        the_gateway.delete_fw_rule(
            protocol,
            dest_port,
            dest_ip,
            source_port,
            source_ip)
        task = the_gateway.save_services_configuration()
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_gateway = self.vca.get_gateway(vdc_name, gateway_name)
        assert the_gateway
        assert the_gateway.get_name() == gateway_name
        rules = the_gateway.get_fw_rules()
        to_find_trait = (
            create_protocol_list(
                self._create_protocols_type(protocol)),
            dest_port,
            dest_ip,
            source_port,
            source_ip)
        rule_found = False
        for rule in rules:
            current_trait = (create_protocol_list(rule.get_Protocols()),
                             rule.get_DestinationPortRange(),
                             rule.get_DestinationIp(),
                             rule.get_SourcePortRange(),
                             rule.get_SourceIp())
            if current_trait == to_find_trait:
                rule_found = True
                break
        assert rule_found == False

    def test_0020(self):
        """Power On vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        assert the_vapp.me.get_status() == 8
        task = the_vapp.poweron()
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp is not None
        assert the_vapp.me.get_status() == 4

    def test_0021(self):
        """Delete vApp Clone"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp'] + '_clone'
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.delete_vapp(vdc_name, vapp_name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp is None

    def test_0022(self):
        """Power Off vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name
        assert the_vapp.me.get_status() == 4
        task = the_vapp.poweroff()
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp is not None
        assert the_vapp.me.get_status() == 8

    def test_0023(self):
        """Delete vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.delete_vapp(vdc_name, vapp_name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp is None

    def test_0024(self):
        """Compose vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        storage_profile = config['vcloud']['storage_profile']

        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        vm_specs = [{
            'template': template,
            'catalog': catalog,
            'name': vm_name,
            'cpus': 3,
            'memory': 4096,
            'storage_profile': storage_profile,
            'guest_customization': {
                'enabled': True,
                'computer_name': vm_name,
                'admin_password_enabled': True,
                'admin_password_auto': True,
                'reset_password_required': True
            }
        }]
        task = self.vca.compose_vapp(
            vdc_name,
            vapp_name,
            network_name=network,
            vm_specs=vm_specs)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vdc = self.vca.get_vdc(vdc_name)
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        assert the_vapp.name == vapp_name

    def test_0025(self):
        """Recompose vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        the_vdc = self.vca.get_vdc(vdc_name)
        storage_profile = config['vcloud']['storage_profile']

        add_vm_specs = [{
            'template': template,
            'catalog': catalog,
            'name': vm_name + '_recompose',
            'cpus': 1,
            'memory': 1024,
            'storage_profile': storage_profile
        }]
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp
        task = self.vca.recompose_vapp(vdc_name, vapp_name,
                                       add_vm_specs=add_vm_specs,
                                       del_vm_specs=[vm_name])
        assert task
        result = self.vca.block_until_completed(task)
        assert result

    def test_0099(self):
        """Delete vApp"""
        vdc_name = config['vcloud']['vdc']
        vapp_name = config['vcloud']['vapp']
        vm_name = config['vcloud']['vm']
        catalog = config['vcloud']['catalog']
        template = config['vcloud']['template']
        network = config['vcloud']['network']
        mode = config['vcloud']['mode']
        the_vdc = self.vca.get_vdc(vdc_name)
        assert the_vdc
        assert the_vdc.get_name() == vdc_name
        task = self.vca.delete_vapp(vdc_name, vapp_name)
        assert task
        result = self.vca.block_until_completed(task)
        assert result
        the_vapp = self.vca.get_vapp(the_vdc, vapp_name)
        assert the_vapp is None
