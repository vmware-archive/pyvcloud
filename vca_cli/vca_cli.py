# VMware vCloud Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# coding: utf-8

import click
import time
import random
import ConfigParser
import os
import yaml
import pkg_resources
import ConfigParser
import logging
import httplib
from os.path import expanduser
from tabulate import tabulate

from pyvcloud.vcloudair import VCA
from pyvcloud.vclouddirector import VCD
from pyvcloud.vapp import VAPP
from pyvcloud.helper import generalHelperFunctions as ghf


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option('-p', '--profile', default='', metavar='<profile>', help='Profile id')
@click.option('-v', '--version', is_flag=True, help='Show version')
@click.option('-d', '--debug', is_flag=True, help='Enable debug')
@click.pass_context
def cli(ctx, profile, version, debug):
    """A command line interface to VMware vCloud."""
    ctx.obj={}
    if profile != '':
        ctx.obj['PROFILE'] = profile
    else:
        config = ConfigParser.RawConfigParser()
        config.read(os.path.expanduser('~/.vcarc'))
        section = 'Global'
        if config.has_option(section, 'profile'):
            ctx.obj['PROFILE'] = config.get(section, 'profile')
        else:
            ctx.obj['PROFILE'] = 'default'        
    
    if debug:
        httplib.HTTPConnection.debuglevel = 1
        logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
    if version:
        version = pkg_resources.require("vca-cli")[0].version
        version_pyvcloud = pkg_resources.require("pyvcloud")[0].version
        click.echo(click.style('vca-cli version %s (pyvcloud: %s)' % (version, version_pyvcloud), fg='blue'))    
    
@cli.command()
@click.pass_context
@click.argument('user')
@click.option('-H', '--host', default='https://vchs.vmware.com')
@click.option('-p', '--password', prompt=True, confirmation_prompt=False,
              hide_input=True)
def login(ctx, user, host, password):
    """Login to a vCloud service"""
    vca = VCA()
    result = vca.login(host, user, password, None)
    if result:
        click.echo(click.style('Login successful with profile \'%s\'' % ctx.obj['PROFILE'], fg='blue'))
        config = ConfigParser.RawConfigParser()  
        config.read(os.path.expanduser('~/.vcarc'))            
        section = 'Profile-%s' % ctx.obj['PROFILE']
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, 'host', host)
        config.set(section, 'user', user)        
        config.set(section, 'token', vca.token)
        with open(os.path.expanduser('~/.vcarc'), 'w+') as configfile:
            config.write(configfile)        
    else:
        click.echo(click.style('login failed', fg='red'))    
    return result
        
def _getVCA(profile='default'):
    vca = VCA()
    try:
        config = ConfigParser.RawConfigParser()
        config.read(os.path.expanduser('~/.vcarc'))
        section = 'Profile-%s' % profile
        if config.has_option(section, "host") and config.has_option(section, "token"):
            host = config.get(section, "host")
            token = config.get(section, "token")
            if vca.login(host, None, None, token):
                return vca
            else:
                print "token expired"
        else:
            print "please authenticate"
    except ConfigParser.Error:
        print "please authenticate"
    return None

@cli.command()
@click.pass_context
def logout(ctx):
    """Logout from a vCloud service"""
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser('~/.vcarc'))
    section = 'Profile-%s' % ctx.obj['PROFILE']
    if config.has_option(section, "host") and config.has_option(section, "token"):
        config.remove_option(section, "token")
        with open(os.path.expanduser('~/.vcarc'), 'w+') as configfile:
            config.write(configfile)     
        click.echo(click.style('logged out user %s' % config.get(section, 'user'), fg='blue'))   
    
@cli.command()
@click.pass_context
def status(ctx):
    """Show current status"""   
    pass
    
def _print_config(config):
    for section in config.sections():
        click.secho(section, fg='green')
        for option in config.options(section):
            click.echo(click.style("%s=" % option, fg='yellow') + click.style("%s" % config.get(section, option), fg='blue'))               
    
#todo: set default profile
@cli.command()
@click.pass_context
@click.argument('operation', default='list', metavar='[list | set | del | select]', type=click.Choice(['list', 'set', 'del', 'select']))
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
@click.option('-g', '--gateway', default='')
def profiles(ctx, operation, service, datacenter, gateway):
    """Configure profiles"""
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser('~/.vcarc'))
    if 'list' == operation:
        _print_config(config)
    elif 'set' == operation:
        section = 'Profile-%s' % ctx.obj['PROFILE']
        if not config.has_section(section):
            config.add_section(section)
        if '' != service:
            config.set(section, 'service', service)
        if '' != datacenter:            
            config.set(section, 'datacenter', datacenter)
        if '' != gateway:    
            config.set(section, 'gateway', gateway)    
        with open(os.path.expanduser('~/.vcarc'), 'w+') as configfile:
            config.write(configfile)
        _print_config(config)
    elif 'del' == operation:
        section = 'Profile-%s' % ctx.obj['PROFILE']
        if config.has_section(section):
            config.remove_section(section)
        with open(os.path.expanduser('~/.vcarc'), 'w+') as configfile:
            config.write(configfile)            
        _print_config(config)
    elif 'select' == operation:
        section = 'Global'
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, 'profile', ctx.obj['PROFILE'])
        with open(os.path.expanduser('~/.vcarc'), 'w+') as configfile:
            config.write(configfile)        
        _print_config(config)        
            
@cli.command(options_metavar='[-s <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | details]', type=click.Choice(['list', 'details']))
@click.option('-s', '--service', default='', metavar='<id>', help='Service id')
def services(ctx, operation, service):
    """Operations with services"""
    vca = _getVCA(ctx.obj['PROFILE'])
    if vca != None:
        services = vca.get_serviceReferences()
        headers = ["ID", "Type", "Region"]
        table = [[serviceReference.get_serviceId(), serviceReference.get_serviceType(), serviceReference.get_region()] for serviceReference in services]
        click.echo(click.style("Available services for '%s' profile:" % ctx.obj['PROFILE'], fg='blue'))   
        print tabulate(table, headers = headers, tablefmt="orgtbl")
        
@cli.command(options_metavar='[-s <id>] [-d <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | details]', type=click.Choice(['list', 'details']))
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
def datacenters(ctx, operation, service, datacenter):
    """Operations with virtual data centers"""
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser('~/.vcarc'))
    section = 'Profile-%s' % ctx.obj['PROFILE'] 
    #todo read config file once only
    if '' == service and config.has_option(section, 'service'):
        service = config.get(section, 'service')
    vca = _getVCA(ctx.obj['PROFILE'])
    if vca != None:        
        if 'list' == operation:
            serviceReferences = vca.get_serviceReferences()
            serviceReferences = filter(lambda serviceReference: serviceReference.get_serviceId().lower() == service.lower(), serviceReferences)
            if serviceReferences:
                table = []
                for serviceReference in serviceReferences:
                    vdcReferences = vca.get_vdcReferences(serviceReference)
                    for vdcReference in vdcReferences:
                            table.append([vdcReference.get_name(), vdcReference.get_status()
                                          ,serviceReference.get_serviceId(), serviceReference.get_serviceType(), serviceReference.get_region()])
                if table:
                    headers = ["Virtual Data Center", "Status"
                                ,"Service ID", "Service Type", "Region"]
                    click.echo(click.style("Available datacenters in service '%s' for '%s' profile:" % (service, ctx.obj['PROFILE']), fg='blue'))                                   
                    print tabulate(table, headers = headers, tablefmt="orgtbl")
                else:
                    print 'VDC(s) not found in this service'
        elif 'details' == operation:
            if '' == datacenter and config.has_option(section, 'datacenter'):
                datacenter = config.get(section, 'datacenter')
            click.echo(click.style("Details for datacenter '%s' in service '%s' for '%s' profile:" % (datacenter, service, ctx.obj['PROFILE']), fg='blue'))                                   
            vdcReference = vca.get_vdcReference(service, datacenter)
            if vdcReference[0] == True:
                # print vdcReference[1].get_name()
                vCloudSession = vca.create_vCloudSession(vdcReference[1])                
                if vCloudSession:
                    vcd = VCD(vCloudSession, service, datacenter)
                    (cpu, memory, storageCapacity) = vcd.get_vdcResources()
                    print "cpu used: %d" % cpu.get_Used()
                    print "mem used: %d" % memory.get_Used()
        else:
            print 'Unknown operation %s' % operation
                    
    else:
        print 'Service(s) not found'
        
@cli.command(options_metavar='[-s <id>] [-d <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | details]', type=click.Choice(['list', 'details']))
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
@click.option('-g', '--gateway', default='')
def gateways(ctx, operation, service, datacenter, gateway):
    """Operations with gateways"""
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser('~/.vcarc'))
    section = 'Profile-%s' % ctx.obj['PROFILE'] 
    #todo read config file once only
    if '' == service and config.has_option(section, 'service'):
        service = config.get(section, 'service')
    if '' == datacenter and config.has_option(section, 'datacenter'):
        datacenter = config.get(section, 'datacenter')     
    vca = _getVCA(ctx.obj['PROFILE'])
    if vca != None:
        vcd = vca.get_vCloudDirector(service, datacenter)
        if vcd != None:
            if 'list' == operation:
                click.secho("Available gateways in datacenter '%s' in service '%s' for '%s' profile:" % (datacenter, service, ctx.obj['PROFILE']), fg='blue')
                gatewayReferences = vcd.get_gateways()
                if gatewayReferences:
                    table = []
                    for gatewayReference in gatewayReferences:
                        table.append([datacenter, gatewayReference.get_name()])
                        if table:
                            headers = ["Datacenter", "Gateway"]
                            print tabulate(table, headers = headers, tablefmt="orgtbl")
                        else:
                            print 'No gateways found in this datacenter'
            elif 'details' == operation:
                if '' == gateway and config.has_option(section, 'gateway'):
                    gateway = config.get(section, 'gateway')
                gatewayReference = vcd.get_gateway(gateway)
                if gatewayReference != None:
                    click.secho("Details for gateway '%s' in datacenter '%s' in service '%s' for '%s' profile:" % (gateway, datacenter, service, ctx.obj['PROFILE']), fg='blue')
                    click.secho('Public IPs', fg='blue')
                    table = []
                    ips = gatewayReference.get_public_ips()
                    iplist = ''
                    for ip in ips:
                        if iplist == '':
                            iplist = ip
                        else:
                            iplist = iplist + ', ' + ip
                    interfaces = gatewayReference.get_uplink_interfaces()
                    intlist = ''
                    for interface in interfaces:
                        if intlist == '':
                            intlist = interface.get_Name()
                        else:
                            intlist = intlist + ', ' + interface.get_Name()
                    table.append([gatewayReference.get_name(), iplist, intlist])
                    headers = ["Gateway", "Public IPs", "Uplink"]
                    print tabulate(table, headers = headers, tablefmt="orgtbl")
                    click.secho('NAT rules', fg='blue')
                    natRules = gatewayReference.get_nat_rules()
                    _print_nat_rules(natRules)
                    # click.secho('Firewall rules', fg='blue')
                else:
                    print 'Gateway not found'
        else:
            print 'Datacenter not found'
    else:
        print 'Service not found'  
        
def _print_nat_rules(natRules):
    result = []
    for natRule in natRules:
        ruleID = natRule.get_Id()
        enable = natRule.get_IsEnabled()
        ruleType = natRule.get_RuleType()
        gatewayNatRule = natRule.get_GatewayNatRule()
        originalIp = gatewayNatRule.get_OriginalIp()
        originalPort = gatewayNatRule.get_OriginalPort()
        translatedIp = gatewayNatRule.get_TranslatedIp()
        translatedPort = gatewayNatRule.get_TranslatedPort()
        protocol = gatewayNatRule.get_Protocol()
        interface = gatewayNatRule.get_Interface().get_name()
        result.append([ruleID, str(enable), ruleType, originalIp, "any" if not originalPort else originalPort,
                      translatedIp, "any" if not translatedPort else translatedPort,
                      "any" if not protocol else protocol, interface])
    if result:
        headers = ["Rule ID", "Enabled", "Type", "Original IP", "Original Port", "Translated IP", "Translated Port", "Protocol", "Applied On"]
        print tabulate(result, headers = headers, tablefmt="orgtbl")
    else:
        print "No NAT rules found in this gateway"
        
@cli.command(options_metavar='[-s <id>] [-d <id>] [-g <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | add | del]', type=click.Choice(['list', 'add', 'del']))
@click.argument('rule_type', default='DNAT', metavar='[DNAT | SNAT]', type=click.Choice(['DNAT', 'SNAT']))
@click.argument('original_ip', default='')
@click.argument('original_port', default='')
@click.argument('translated_ip', default='')
@click.argument('translated_port', default='')
@click.argument('protocol', default='')
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
@click.option('-g', '--gateway', default='')
def nat(ctx, operation, service, datacenter, gateway, rule_type, original_ip, original_port, translated_ip, translated_port, protocol):
    """Operations with gateway NAT rules"""
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser('~/.vcarc'))
    section = 'Profile-%s' % ctx.obj['PROFILE'] 
    #todo read config file once only
    if '' == service and config.has_option(section, 'service'):
        service = config.get(section, 'service')
    if '' == datacenter and config.has_option(section, 'datacenter'):
        datacenter = config.get(section, 'datacenter')     
    vca = _getVCA(ctx.obj['PROFILE'])
    if vca != None:
        vcd = vca.get_vCloudDirector(service, datacenter)
        if vcd != None:
            if '' == gateway and config.has_option(section, 'gateway'): 
                gateway = config.get(section, 'gateway')
            gatewayReference = vcd.get_gateway(gateway)
            
            if 'list' == operation:
                print 'list of dnat rules'
            elif 'add' == operation:
                print 'adding dnat rule'
                if gatewayReference != None:
                    result = gatewayReference.add_nat_rule(rule_type, original_ip, original_port, translated_ip, translated_port, protocol)
                    if result[0]:
                        vcd.get_task(result[1], 'table')
            elif 'del' == operation:
                print 'deleting dnat rule'
                if gatewayReference != None:
                    result = gatewayReference.del_nat_rule(rule_type, original_ip, original_port, translated_ip, translated_port, protocol)
                    if result[0]:
                        vcd.get_task(result[1], 'table')
            if gatewayReference != None:
                natRules = gatewayReference.get_nat_rules()
                _print_nat_rules(natRules)            
            else:
                print 'Gateway not found'                
        else:
            print 'Gateway not found'

@cli.command(options_metavar='[-s <id>] [-d <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | add]', type=click.Choice(['list', 'add']))
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
def networks(ctx, operation, service, datacenter):
    """Operations with networks"""
    pass
    
@cli.command(options_metavar='[-s <id>] [-d <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | details]', type=click.Choice(['list', 'details']))
@click.argument('taskid', default='', metavar='[TASK-ID]')
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
def tasks(ctx, operation, service, datacenter, taskid):
    """Operations with tasks"""
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser('~/.vcarc'))
    section = 'Profile-%s' % ctx.obj['PROFILE'] 
    #todo read config file once only
    if '' == service and config.has_option(section, 'service'):
        service = config.get(section, 'service')
    if '' == datacenter and config.has_option(section, 'datacenter'):
        datacenter = config.get(section, 'datacenter')     
    vca = _getVCA(ctx.obj['PROFILE'])
    if vca != None:
        vcd = vca.get_vCloudDirector(service, datacenter)
        if vcd != None:
            if 'list' == operation:
                print 'list of tasks'
                taskRecords = vcd.get_tasks()
                table = []
                for taskRecord in taskRecords:
                    id = taskRecord.get_href()[taskRecord.get_href().rindex('/')+1:]
                    table.append([taskRecord.get_name(), taskRecord.get_status(), taskRecord.get_endDate(), id])
                import operator
                tt = sorted(table, key=operator.itemgetter(2), reverse=True)
                t = []
                i = 0
                for row in tt:
                    i = i + 1
                    t.append([i] + row)
                headers = ["Name", "Status", "End Date", "id"]
                print tabulate(t, headers = headers, tablefmt="orgtbl")                
            elif 'details' == operation:
                print "details about task '%s'" % taskid
                vcd.get_task_from_id(taskid, 'table')
                
@cli.command(options_metavar='[-s <id>] [-d <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | details | power.on | power.off | reboot | create]', type=click.Choice(['list', 'details', 'power.on', 'power.off', 'reboot', 'create']))
@click.argument('vapp', default='', metavar='[vAPP]')
@click.argument('template', default='', metavar='[TEMPLATE]')
@click.argument('catalog', default='', metavar='[CATALOG]')
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
def vapps(ctx, operation, service, datacenter, vapp, template, catalog):
    """Operations with vApps"""
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser('~/.vcarc'))
    section = 'Profile-%s' % ctx.obj['PROFILE'] 
    #todo read config file once only
    if '' == service and config.has_option(section, 'service'):
        service = config.get(section, 'service')
    if '' == datacenter and config.has_option(section, 'datacenter'):
        datacenter = config.get(section, 'datacenter')     
    vca = _getVCA(ctx.obj['PROFILE'])
    if vca != None:
        vcd = vca.get_vCloudDirector(service, datacenter)
        if vcd != None:
            if 'list' == operation:
                print 'list of vApps'
                table = [[vcd.service,vcd.vdc,vApp.get_name(), ghf.status[vApp.get_status()](), vApp.get_Owner().get_User().get_name(),
                    vApp.get_DateCreated().strftime("%d/%m/%Y %H:%M:%S")] for vApp in vcd.get_vApps()]
                headers = ["Service", "Datacenter", "vApp", "Status", "Owner", "Date Created"]
                print tabulate(table, headers = headers, tablefmt="orgtbl")                
            elif 'details' == operation:
                print "details about vApp '%s'" % vapp
                vApp = vcd.get_vApp(vapp)
                if vApp != None:
                    table = []
                    for description in vApp.details_of_vms():
                        table.append([vcd.service, vcd.vdc, vApp.name] + description)                
                    headers = ["Service", "Datacenter", "vApp", "VM", "Status", "CPU", "Memory", "OS", "Owner"]
                    print tabulate(table, headers = headers, tablefmt="orgtbl")
            elif 'power.on' == operation:
                print "power on vApp '%s'" % vapp
                vApp = vcd.get_vApp(vapp)
                if vApp != None:
                    vApp.poweron({'--blocking': True, '--json': True})                    
            elif 'power.off' == operation:
                print "power off vApp '%s'" % vapp
                vApp = vcd.get_vApp(vapp)
                if vApp != None:
                    vApp.poweroff({'--blocking': True, '--json': True})
            elif 'reboot' == operation:
                print "reboot vApp '%s'" % vapp
                vApp = vcd.get_vApp(vapp)
                if vApp != None:
                    vApp.reboot({'--blocking': True, '--json': True})
            elif 'create' == operation:
                print "create vApp '%s' from template %s in catalog %s" % (vapp, template, catalog)
                        
@cli.command(options_metavar='[-s <id>] [-d <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | details]', type=click.Choice(['list', 'details']))
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
def catalogs(ctx, operation, service, datacenter):
    """Operations with catalogs"""
    pass

@cli.command(options_metavar='[-s <id>] [-d <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | details]', type=click.Choice(['list', 'details']))
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
def templates(ctx, operation, service, datacenter):
    """Operations with templates"""
    pass

@cli.command(options_metavar='[-s <id>] [-d <id>]')
@click.pass_context
@click.argument('operation', default='list', metavar='[list | details]', type=click.Choice(['list', 'details']))
@click.option('-s', '--service', default='')
@click.option('-d', '--datacenter', default='')
def disks(ctx, operation, service, datacenter):
    """Operations with disks"""
    pass
    
                

if __name__ == '__main__':
    cli(obj={})
