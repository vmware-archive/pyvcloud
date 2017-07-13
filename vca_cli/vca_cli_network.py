# vCloud Air CLI 0.1
#
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
#
# This product is licensed to you under the
# Apache License, Version 2.0 (the "License").
# You may not use this product except in compliance with the License.
#
# This product may include a number of subcomponents with
# separate copyright notices and license terms. Your use of the source
# code for the these subcomponents is subject to the terms and
# conditions of the subcomponent's license, as noted in the LICENSE file.
#

import click
from pyvcloud.schema.vcd.v1_5.schemas.vcloud.vcloudType import parseString
import sys
from vca_cli import cli
from vca_cli import default_operation
from vca_cli import utils
import yaml


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[info | list | use | set-syslog'
                        ' | add-ip | del-ip]',
                type=click.Choice(['info', 'list',
                                   'use', 'set-syslog',
                                   'add-ip', 'del-ip']))
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-g', '--gateway', default=None,
              metavar='<gateway>', help='Edge Gateway Name')
@click.option('-i', '--ip', default='', metavar='<ip>', help='IP address')
def gateway(cmd_proc, operation, vdc, gateway, ip):
    """Operations with Edge Gateway"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if vdc is None:
        vdc = cmd_proc.vdc_name
    the_vdc = cmd_proc.vca.get_vdc(vdc)
    if the_vdc is None:
        utils.print_error("VDC not found '%s'" % vdc, cmd_proc)
        sys.exit(1)
    if gateway is None:
        gateway = cmd_proc.gateway
    the_gateway = cmd_proc.vca.get_gateway(vdc, gateway)
    if the_gateway is None:
        utils.print_error("gateway not found '%s'" % gateway, cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        headers = ['Name', 'External IPs', 'DHCP', 'Firewall', 'NAT',
                   'VPN', 'Routed Networks', 'Syslog', 'Uplinks', 'Selected']
        gateways = cmd_proc.vca.get_gateways(vdc)
        table = cmd_proc.gateways_to_table(gateways)
        if cmd_proc.json_output:
            json_object = {'gateways':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Available gateways in '%s', profile '%s':" %
                              (vdc, cmd_proc.profile),
                              headers, table, cmd_proc)
    elif ('use' == operation or
          'info' == operation or
          'set-syslog' == operation or
          'add-ip' == operation or
          'del-ip' == operation):
        if 'set-syslog' == operation:
            task = the_gateway.set_syslog_conf(ip)
            if task:
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                error = parseString(the_gateway.response.content, True)
                utils.print_error("can't set syslog server: " +
                                  error.get_message(), cmd_proc)
                sys.exit(1)
        elif 'add-ip' == operation:
            utils.print_message("allocating public IP for gateway '%s' "
                                "in VDC '%s'" %
                                (gateway, vdc), cmd_proc)
            task = the_gateway.allocate_public_ip()
            if task:
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                error = parseString(the_gateway.response.content, True)
                utils.print_error("can't allocate public IP: " +
                                  error.get_message(), cmd_proc)
                sys.exit(1)
        elif 'del-ip' == operation:
            utils.print_message("deallocating public IP '%s' from gateway "
                                "'%s' in VDC '%s'" %
                                (ip, gateway, vdc), cmd_proc)
            task = the_gateway.deallocate_public_ip(ip)
            if task:
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                error = parseString(the_gateway.response.content, True)
                utils.print_error("can't deallocate public IP: " +
                                  error.get_message(), cmd_proc)
                sys.exit(1)
        elif 'use' == operation:
            cmd_proc.gateway = gateway
            utils.print_message("Selected gateway '%s'" % gateway, cmd_proc)
        elif 'info' == operation:
            headers = ['Property', 'Value']
            table = cmd_proc.gateway_to_table(the_gateway)
            if cmd_proc.json_output:
                json_object = {'gateway':
                               utils.table_to_json(headers, table)}
                utils.print_json(json_object, cmd_proc=cmd_proc)
            else:
                utils.print_table("Details of gateway '%s' in VDC '%s', "
                                  "profile '%s':" %
                                  (gateway, vdc, cmd_proc.profile),
                                  headers, table, cmd_proc)
    else:
        utils.print_error('not implemented', cmd_proc)
        sys.exit(1)
    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | create | delete]',
                type=click.Choice(['list', 'info', 'create', 'delete']))
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-g', '--gateway', default=None, metavar='<gateway>',
              help='Edge Gateway Name')
@click.option('-n', '--network', 'network_name', default='',
              metavar='<network>', help='Network name')
@click.option('-i', '--gateway-ip', 'gateway_ip', default='',
              metavar='<gateway-ip>', help='Gateway IP')
@click.option('-m', '--netmask', default='',
              metavar='<netmask>', help='Network mask')
@click.option('-1', '--dns1', default='',
              metavar='<dns-1>', help='Primary DNS')
@click.option('-2', '--dns2', default='',
              metavar='<dns-2>', help='Secondary DNS')
@click.option('-s', '--suffix', 'dns_suffix', default='',
              metavar='<suffix>', help='DNS suffix')
@click.option('-p', '--pool', default='',
              metavar='<pool-range>', help='Static IP pool')
def network(cmd_proc, operation, vdc, gateway, network_name, gateway_ip,
            netmask, dns1, dns2, dns_suffix, pool):
    """Operations with Networks"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if vdc is None:
        vdc = cmd_proc.vdc_name
    the_vdc = cmd_proc.vca.get_vdc(vdc)
    if the_vdc is None:
        utils.print_error("VDC not found '%s'" % vdc, cmd_proc)
        sys.exit(1)
    if gateway is None:
        gateway = cmd_proc.gateway
    the_gateway = cmd_proc.vca.get_gateway(vdc, gateway)
    if the_gateway is None:
        utils.print_error("gateway not found '%s'" % gateway, cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        headers = ['Name', 'Mode', 'Gateway', 'Netmask', 'DNS 1', 'DNS 2',
                   'Pool IP Range']
        networks = cmd_proc.vca.get_networks(vdc)
        table = cmd_proc.networks_to_table(networks)
        if cmd_proc.json_output:
            json_object = {'networks':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Available networks in '%s', profile '%s':" %
                              (vdc, cmd_proc.profile),
                              headers, table, cmd_proc)
    elif 'create' == operation:
        utils.print_message("Creating network '%s' "
                            "in VDC '%s'" %
                            (network_name, vdc), cmd_proc)
        start_address = pool.split('-')[0]
        end_address = pool.split('-')[1]
        result = cmd_proc.vca.create_vdc_network(vdc, network_name,
                                                 gateway,
                                                 start_address, end_address,
                                                 gateway_ip,
                                                 netmask, dns1, dns2,
                                                 dns_suffix)
        if result[0]:
            utils.display_progress(result[1], cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            utils.print_error("can't create network", cmd_proc)
            sys.exit(1)
    elif 'delete' == operation:
        result = cmd_proc.vca.delete_vdc_network(vdc, network_name)
        if result[0]:
            utils.display_progress(result[1], cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            utils.print_error("can't delete network", cmd_proc)
            sys.exit(1)
    else:
        utils.print_error('not implemented', cmd_proc)
        sys.exit(1)
    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | enable | disable | add | delete]',
                type=click.Choice(['list', 'enable', 'disable', 'add',
                                   'delete']))
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-g', '--gateway', default=None, metavar='<gateway>',
              help='Edge Gateway Name')
@click.option('--enable/--disable', 'is_enable', default=True,
              help='Firewall rule enabled')
@click.option('--description', 'description', default=None,
              metavar='<description>', help='Rule description')
@click.option('--policy', 'policy', default='allow',
              metavar='<policy>', help='Rule policy',
              type=click.Choice(['drop', 'allow']))
@click.option('--protocol', 'protocol', default='tcp',
              metavar='<protocol>', help='Rule protocol',
              type=click.Choice(['tcp', 'udp', 'icmp', 'any']))
@click.option('--dest-port', 'dest_port', default='',
              metavar='<dest_port>', help='Destination port')
@click.option('--dest-ip', 'dest_ip', default='',
              metavar='<dest_ip>', help='Destination IP/range')
@click.option('--source-port', 'source_port', default='',
              metavar='<source_port>', help='Source port')
@click.option('--source-ip', 'source_ip', default='',
              metavar='<source_ip>', help='Source IP/range')
@click.option('--logging/--no-logging', 'enable_logging', default=True,
              help='Enable logging for rule')
@click.option('-f', '--file', 'fw_rules_file',
              default=None, metavar='<fw_rules_file>',
              help='Firewall rules file',
              type=click.File('r'))
def firewall(cmd_proc, operation, vdc, gateway, is_enable, description, policy,
             protocol, dest_port, dest_ip, source_port, source_ip,
             enable_logging, fw_rules_file):
    """Operations with Edge Gateway Firewall Service"""

    def proto(name):
        return name[0].upper() + name[1:].lower()

    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if vdc is None:
        vdc = cmd_proc.vdc_name
    the_vdc = cmd_proc.vca.get_vdc(vdc)
    if the_vdc is None:
        utils.print_error("VDC not found '%s'" % vdc, cmd_proc)
        sys.exit(1)
    if gateway is None:
        gateway = cmd_proc.gateway
    the_gateway = cmd_proc.vca.get_gateway(vdc, gateway)
    if the_gateway is None:
        utils.print_error("gateway not found '%s'" % gateway, cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        headers = ['Description', 'Source IP', 'Source Port', 'Destination IP',
                   'Destination Port', 'Protocol', 'Enabled']
        table = cmd_proc.firewall_rules_to_table(the_gateway)
        if cmd_proc.json_output:
            json_object = {'fw-rules':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Firewall rules in gateway '%s', "
                              "VDC '%s', profile '%s' (firewall is %s):" %
                              (gateway, vdc, cmd_proc.profile,
                               'On' if the_gateway.is_fw_enabled()
                               else 'Off'),
                              headers, table, cmd_proc)
    elif 'enable' == operation or 'disable' == operation:
        utils.print_message("%s firewall" % operation)
        the_gateway.enable_fw('enable' == operation)
        task = the_gateway.save_services_configuration()
        if task:
            utils.display_progress(task,
                                   cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            error = parseString(the_gateway.response.content, True)
            utils.print_error("can't '%s' the firewall: " % operation +
                              error.get_message(), cmd_proc)
            sys.exit(1)
    elif 'add' == operation:
        utils.print_message("add firewall rule")
        if fw_rules_file:
            rules = yaml.load(fw_rules_file)
            if rules and rules[0]:
                fw_rules = rules[0].get('Firewall_rules')
                for rule in fw_rules:
                    # Take defaults for is_enable, policy, protocol and
                    # enable_logging from cmdline switches (or their defaults)
                    the_gateway.add_fw_rule(rule.get('is_enable', is_enable),
                                            rule.get('description', None),
                                            rule.get('policy', policy),
                                            proto(
                                                rule.get('protocol', protocol)
                                                ),
                                            rule.get('dest_port'),
                                            rule.get('dest_ip'),
                                            rule.get('source_port'),
                                            rule.get('source_ip'),
                                            rule.get('enable_logging',
                                                     enable_logging))
        else:
            the_gateway.add_fw_rule(is_enable, description, policy,
                                    proto(protocol),
                                    dest_port, dest_ip, source_port, source_ip,
                                    enable_logging)
        task = the_gateway.save_services_configuration()
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            error = parseString(the_gateway.response.content, True)
            utils.print_error("can't add firewall rule: " +
                              error.get_message(), cmd_proc)
            sys.exit(1)
    elif 'delete' == operation:
        utils.print_message("delete firewall rule")
        if fw_rules_file:
            rules = yaml.load(fw_rules_file)
            if rules and rules[0]:
                fw_rules = rules[0].get('Firewall_rules')
                for rule in fw_rules:
                    # Take default for protocol cmdline switch (or its default)
                    the_gateway.delete_fw_rule(proto(
                                               rule.get('protocol', protocol)
                                               ),
                                               str(rule.get('dest_port')),
                                               rule.get('dest_ip'),
                                               str(rule.get('source_port')),
                                               rule.get('source_ip'))
        else:
            the_gateway.delete_fw_rule(proto(protocol), dest_port, dest_ip,
                                       source_port, source_ip)
        task = the_gateway.save_services_configuration()
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            error = parseString(the_gateway.response.content, True)
            utils.print_error("can't delete firewall rule: " +
                              error.get_message(), cmd_proc)
            sys.exit(1)

    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | add | delete | enable | disable]',
                type=click.Choice(['list', 'add',
                                   'delete', 'enable', 'disable']))
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-g', '--gateway', default=None, metavar='<gateway>',
              help='Edge Gateway Name')
@click.option('-n', '--network', 'network_name', default='',
              metavar='<network>', help='Network name')
@click.option('-p', '--pool', default='',
              metavar='<pool-range>', help='DHCP pool range')
def dhcp(cmd_proc, operation, vdc, gateway, network_name, pool):
    """Operations with Edge Gateway DHCP Service"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if vdc is None:
        vdc = cmd_proc.vdc_name
    the_vdc = cmd_proc.vca.get_vdc(vdc)
    if the_vdc is None:
        utils.print_error("VDC not found '%s'" % vdc, cmd_proc)
        sys.exit(1)
    if gateway is None:
        gateway = cmd_proc.gateway
    the_gateway = cmd_proc.vca.get_gateway(vdc, gateway)
    if the_gateway is None:
        utils.print_error("gateway not found '%s'" % gateway, cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        headers = ['Network', 'IP Range From', 'To',
                   'Enabled', 'Default lease', 'Max Lease']
        table = cmd_proc.dhcp_to_table(the_gateway)
        if cmd_proc.json_output:
            json_object = {'dhcp-pools':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("DHCP pools in gateway '%s', "
                              "VDC '%s', profile '%s':" %
                              (gateway, vdc, cmd_proc.profile),
                              headers, table, cmd_proc)
    elif 'add' == operation:
        utils.print_message("adding DHCP pool to network '%s'" %
                            network_name,
                            cmd_proc)
        the_gateway.add_dhcp_pool(network_name, pool.split('-')[0],
                                  pool.split('-')[1], default_lease=None,
                                  max_lease=None)
        task = the_gateway.save_services_configuration()
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            error = parseString(the_gateway.response.content, True)
            utils.print_error("can't add DHCP pool: " +
                              error.get_message(), cmd_proc)
            sys.exit(1)
    elif 'delete' == operation:
        utils.print_message("deleting all DHCP pools in network '%s'" %
                            network_name)
        the_gateway.delete_dhcp_pool(network_name)
        task = the_gateway.save_services_configuration()
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            utils.print_error("can't delete DHCP pool", cmd_proc)
            sys.exit(1)
    elif 'enable' == operation or 'disable' == operation:
        utils.print_message("%s DHCP service" % operation)
        the_gateway.enable_dhcp('enable' == operation)
        task = the_gateway.save_services_configuration()
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            error = parseString(the_gateway.response.content, True)
            utils.print_error("can't '%s' the DHCP service: " % operation +
                              error.get_message(), cmd_proc)
    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | add | delete]',
                type=click.Choice(['list', 'add', 'delete']))
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-g', '--gateway', default=None, metavar='<gateway>',
              help='Edge Gateway Name')
@click.option('--type', 'rule_type', default='DNAT',
              metavar='<type>', help='Rule type',
              type=click.Choice(['DNAT', 'dnat', 'SNAT', 'snat']))
@click.option('--original-ip', 'original_ip', default='',
              metavar='<ip>', help='Original IP')
@click.option('--original-port', 'original_port',
              default='any', metavar='<port>',
              help='Original Port')
@click.option('--translated-ip', 'translated_ip',
              default='', metavar='<ip>',
              help='Translated IP')
@click.option('--translated-port', 'translated_port',
              default='any', metavar='<port>',
              help='Translated Port')
@click.option('--protocol', default='any',
              metavar='<protocol>', help='Protocol',
              type=click.Choice(['any', 'Any', 'tcp', 'udp']))
@click.option('-n', '--network', 'network_name', default=None,
              metavar='<network>', help='Network name')
@click.option('-f', '--file', 'nat_rules_file',
              default=None, metavar='<nat_rules_file>',
              help='NAT rules file',
              type=click.File('r'))
@click.option('-a', '--all', 'all_rules', is_flag=True, default=False,
              help='Delete all rules')
def nat(cmd_proc, operation, vdc, gateway, rule_type, original_ip,
        original_port, translated_ip, translated_port, protocol,
        network_name, nat_rules_file, all_rules):
    """Operations with Edge Gateway NAT Rules"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if vdc is None:
        vdc = cmd_proc.vdc_name
    the_vdc = cmd_proc.vca.get_vdc(vdc)
    if the_vdc is None:
        utils.print_error("VDC not found '%s'" % vdc, cmd_proc)
        sys.exit(1)
    if gateway is None:
        gateway = cmd_proc.gateway
    the_gateway = cmd_proc.vca.get_gateway(vdc, gateway)
    if the_gateway is None:
        utils.print_error("gateway not found '%s'" % gateway, cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        headers = ["Rule Id", "Enabled", "Type", "Original IP",
                   "Original Port", "Translated IP", "Translated Port",
                   "Protocol", "Applied On"]
        table = cmd_proc.nat_rules_to_table(the_gateway)
        if cmd_proc.json_output:
            json_object = {'nat-rules':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("NAT rules in gateway '%s', "
                              "VDC '%s', profile '%s':" %
                              (gateway, vdc, cmd_proc.profile),
                              headers, table, cmd_proc)
    elif 'add' == operation:
        utils.print_message("add NAT rule")
        if nat_rules_file:
            rules = yaml.load(nat_rules_file)
            if rules and rules[0]:
                nat_rules = rules[0].get('NAT_rules')
                for rule in nat_rules:
                    the_gateway.add_nat_rule(rule.get('type').upper(),
                                             rule.get('original_ip'),
                                             rule.get('original_port'),
                                             rule.get('translated_ip'),
                                             rule.get('translated_port'),
                                             rule.get('protocol'),
                                             rule.get('network_name'))
        else:
            the_gateway.add_nat_rule(rule_type.upper(),
                                     original_ip,
                                     original_port,
                                     translated_ip,
                                     translated_port,
                                     protocol,
                                     network_name)
        task = the_gateway.save_services_configuration()
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            error = parseString(the_gateway.response.content, True)
            utils.print_error("can't add NAT rule: " +
                              error.get_message(), cmd_proc)
            sys.exit(1)
    elif 'delete' == operation:
        utils.print_message("delete NAT rule")
        found_rule = False
        if all_rules:
            the_gateway.del_all_nat_rules()
            found_rule = True
        else:
            found_rule = the_gateway.del_nat_rule(rule_type.upper(),
                                                  original_ip,
                                                  original_port,
                                                  translated_ip,
                                                  translated_port,
                                                  protocol,
                                                  network_name)
        if found_rule:
            task = the_gateway.save_services_configuration()
            if task:
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                error = parseString(the_gateway.response.content, True)
                utils.print_error("can't delete NAT rule: " +
                                  error.get_message(), cmd_proc)
                sys.exit(1)
        else:
            utils.print_error("rule doesn't exist in edge gateway", cmd_proc)
            sys.exit(1)
    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | enable | disable | add-endpoint'
                        ' | del-endpoint | add-tunnel | del-tunnel'
                        ' | add-network | del-network]',
                type=click.Choice(
                    ['list', 'enable', 'disable', 'add-endpoint',
                     'del-endpoint', 'add-tunnel', 'del-tunnel',
                     'add-network', 'del-network']))
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-g', '--gateway', default=None, metavar='<gateway>',
              help='Edge Gateway Name')
@click.option('-n', '--network', 'network_name', default='',
              metavar='<network>', help='Network name')
@click.option('-p', '--public-ip', 'public_ip', default='',
              metavar='<ip_address>', help='Public IP address')
@click.option('-t', '--tunnel', default='',
              metavar='<tunnel>', help='Tunnel name')
@click.option('-i', '--local-ip', 'local_ip', default='',
              metavar='<ip_address>', help='Local IP address')
@click.option('-w', '--local-network', 'local_network', default=None,
              metavar='<network>', help='Local network')
@click.option('-e', '--peer-ip', 'peer_ip', default='',
              metavar='<ip_address>', help='Peer IP address')
@click.option('-k', '--peer-network', 'peer_network', default=None,
              metavar='<network>', help='Peer network')
@click.option('-s', '--secret', default='', metavar='<secret>',
              help='Shared secret')
def vpn(cmd_proc, operation, vdc, gateway, network_name, public_ip, local_ip,
        local_network, peer_ip, peer_network, tunnel, secret):
    """Operations with Edge Gateway VPN"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if vdc is None:
        vdc = cmd_proc.vdc_name
    the_vdc = cmd_proc.vca.get_vdc(vdc)
    if the_vdc is None:
        utils.print_error("VDC not found '%s'" % vdc, cmd_proc)
        sys.exit(1)
    if gateway is None:
        gateway = cmd_proc.gateway
    the_gateway = cmd_proc.vca.get_gateway(vdc, gateway)
    if the_gateway is None:
        utils.print_error("gateway not found '%s'" % gateway, cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        headers1 = ['EndPoint', 'Public IP']
        table1 = cmd_proc.vpn_endpoints_to_table(the_gateway)
        headers2 = ['Tunnel', 'Local IP', 'Local Networks', 'Peer IP',
                    'Peer Networks', 'Enabled', 'Operational']
        table2 = cmd_proc.vpn_tunnels_to_table(the_gateway)
        if cmd_proc.json_output:
            json_object = {'endpoints': table1, 'tunnels': table2}
            utils.print_json(json_object, 'VPN config',
                             cmd_proc)
        else:
            utils.print_table("VPN endpoints in gateway '%s', "
                              "VDC '%s', profile '%s':" %
                              (gateway, vdc, cmd_proc.profile),
                              headers1, table1, cmd_proc)
            utils.print_table("VPN tunnels in gateway '%s', "
                              "VDC '%s', profile '%s':" %
                              (gateway, vdc, cmd_proc.profile),
                              headers2, table2, cmd_proc)
    else:
        if 'enable' == operation or 'disable' == operation:
            utils.print_message("%s VPN service" % operation)
            the_gateway.enable_vpn('enable' == operation)
        elif 'add-endpoint' == operation:
            utils.print_message("add VPN endpoint")
            the_gateway.add_vpn_endpoint(network_name, public_ip)
        elif 'del-endpoint' == operation:
            utils.print_message("delete VPN endpoint")
            the_gateway.del_vpn_endpoint(network_name, public_ip)
        elif 'add-tunnel' == operation:
            utils.print_message("add VPN tunnel")
            the_gateway.add_vpn_tunnel(tunnel, local_ip, local_network,
                                       peer_ip, peer_network, secret)
        elif 'del-tunnel' == operation:
            utils.print_message("delete VPN tunnel")
            the_gateway.delete_vpn_tunnel(tunnel)
        elif 'add-network' == operation:
            utils.print_message("add network to VPN tunnel")
            the_gateway.add_network_to_vpn_tunnel(tunnel, local_network,
                                                  peer_network)
        elif 'del-network' == operation:
            utils.print_message("delete network from VPN tunnel")
            the_gateway.delete_network_from_vpn_tunnel(tunnel, local_network,
                                                       peer_network)
        task = the_gateway.save_services_configuration()
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            error = parseString(the_gateway.response.content, True)
            utils.print_error("can't update VPN configuration: " +
                              error.get_message(), cmd_proc)
            sys.exit(1)
    cmd_proc.save_current_config()
