# vCloud Air CLI 0.1
# 
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
#
# This product is licensed to you under the Apache License, Version 2.0 (the "License").  
# You may not use this product except in compliance with the License.  
#
# This product may include a number of subcomponents with
# separate copyright notices and license terms. Your use of the source
# code for the these subcomponents is subject to the terms and
# conditions of the subcomponent's license, as noted in the LICENSE file. 
#
# coding: utf-8

import sys
import operator
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
import json
import requests
import xmltodict
from os.path import expanduser
from tabulate import tabulate
from time import sleep
from StringIO import StringIO

from pyvcloud.vcloudair import VCA
from pyvcloud.vcloudsession import VCS
from pyvcloud.helper import CommonUtils

from pyvcloud.schema.vcd.v1_5.schemas.vcloud import taskType

#todo: print vApp in json format
#todo: include network config during the instantiation to instantiate vm and connect in one shot
#todo: list tasks
#todo: catalogs, details
#todo: replace network config instead of adding
#todo: configurable profile file ~/.vcarc
#todo: consider default list or info
#todo: consider add the selectors --service --org, --vdc, --gateway... at the root and pass by ctx
#todo: reuse vcloud session token between calls
#todo: command to update session to avoid timeouts, if possible
#todo: OnDemand create instance and create vdc, use templates
#todo: OnDemand plan command, billing mettering and instance creation
#todo: store and display status of the vcloud org_url
#todo: catch exceptions
#todo: vapp command returns nothing no error when session is inactive on subscription

properties = ['session_token', 'org', 'org_url', 'service', 'vdc', 'instance', 'service_type', 'service_version', 'token', 'user', 'host', 'gateway', 'session_uri', 'verify']

default_operation = 'list'

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option('-p', '--profile', default='', metavar='<profile>', help='Profile id')
@click.option('-v', '--version', is_flag=True, help='Show version')
@click.option('-d', '--debug', is_flag=True, help='Enable debug')
@click.option('-j', '--json', 'json_output', is_flag=True, help='Results as JSON object')
@click.option('-x', '--xml', 'xml_output', is_flag=True, help='Results as XML document')
@click.option('-i', '--insecure', is_flag=True, help='Perform insecure SSL connections')
@click.pass_context
def cli(ctx, profile, version, debug, json_output, xml_output, insecure):
    """VMware vCloud Air Command Line Interface."""
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser('~/.vcarc'))    
    ctx.obj={}
    if profile != '':
        ctx.obj['profile'] = profile
    else:
        section = 'Global'
        if config.has_option(section, 'profile'):
            ctx.obj['profile'] = config.get(section, 'profile')
        else:
            ctx.obj['profile'] = 'default'    
   
    section = 'Profile-%s' % ctx.obj['profile']    
    for prop in properties:
        ctx.obj[prop] = config.get(section, prop) if config.has_option(section, prop) else ''
        if ctx.obj[prop] == 'None': ctx.obj[prop] = None
        if ctx.obj[prop] == 'True': ctx.obj[prop] = True
        if ctx.obj[prop] == 'False': ctx.obj[prop] = False
        
    ctx.obj['verify'] = not insecure
    ctx.obj['json_output'] = json_output
    ctx.obj['xml_output'] = xml_output

    if debug:
        httplib.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
    if version:
        version = pkg_resources.require("vca-cli")[0].version
        version_pyvcloud = pkg_resources.require("pyvcloud")[0].version
        print_message('vca-cli version %s (pyvcloud: %s)' % (version, version_pyvcloud), ctx.obj['json_output'])
    else:
        if ctx.invoked_subcommand is None:
               help_text = ctx.get_help()
               print help_text        

def _save_property(profile, property, value):               
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser('~/.vcarc'))
    section = 'Profile-%s' % profile
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, property, value)
    with open(os.path.expanduser('~/.vcarc'), 'w+') as configfile:
        config.write(configfile)    
    
#todo: add --list-vdcs / orgs    
@cli.command()
@click.pass_context
@click.argument('user')
@click.option('-t', '--type', 'service_type', default='ondemand', metavar='[subscription | ondemand | vcd]', type=click.Choice(['subscription', 'ondemand', 'vcd']), help='')
@click.option('-v', '--version', 'service_version', default='5.7', metavar='[5.5 | 5.6 | 5.7]', type=click.Choice(['5.5', '5.6', '5.7']), help='')
@click.option('-H', '--host', default='https://iam.vchs.vmware.com', help='')
@click.option('-p', '--password', prompt=True, confirmation_prompt=False, hide_input=True, help='Password')
@click.option('-i', '--instance', default=None, help='Instance Id')
@click.option('-o', '--org', default=None, help='Organization Name')
def login(ctx, user, host, password, service_type, service_version, instance, org):
    """Login to a vCloud service"""
    if not (host.startswith('https://') or host.startswith('http://')):
        host = 'https://' + host   
    vca = VCA(host, user, service_type, service_version, ctx.obj['verify'])
    result = vca.login(password=password, org=org)
    if result:
        if instance:
            result = vca.login_to_instance(instance, password, None, None)
        if result:        
            print_message('Login successful for profile \'%s\'' % ctx.obj['profile'], ctx.obj['json_output'])
            config = ConfigParser.RawConfigParser()
            config.read(os.path.expanduser('~/.vcarc'))
            section = 'Profile-%s' % ctx.obj['profile']
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, 'host', host)
            config.set(section, 'user', user)
            config.set(section, 'token', vca.token)
            config.set(section, 'service_type', service_type)
            config.set(section, 'service_version', service_version)
            if instance:
                config.set(section, 'instance', instance)
                config.set(section, 'org_url', vca.vcloud_session.org_url)
            if vca.vcloud_session:
                config.set(section, 'session_token', vca.vcloud_session.token)                
            if org:
                config.set(section, 'org', org)                
                config.set(section, 'org_url', vca.vcloud_session.org_url)
            else:
                config.set(section, 'org', None)                
                if not instance: config.set(section, 'org_url', None)
            with open(os.path.expanduser('~/.vcarc'), 'w+') as configfile:
                config.write(configfile)
    if not result:
        print_error('login failed', ctx.obj['json_output'])
    return result
    
@cli.command()
@click.pass_context
def logout(ctx):
    """Logout from a vCloud service"""
    vca = _getVCA(ctx)
    if vca:
        vca.logout()
    _save_property(ctx.obj['profile'], 'token', 'None')
    _save_property(ctx.obj['profile'], 'session_token', 'None') 
    _save_property(ctx.obj['profile'], 'org_url', 'None')    
    _save_property(ctx.obj['profile'], 'session_uri', 'None')
    # _save_property(ctx.obj['profile'], 'vdc', 'None')
    print_message('Logout successful for profile \'%s\'' % ctx.obj['profile'], ctx.obj['json_output'])        
    
@cli.command()
@click.pass_context
def status(ctx):
    """Show current status"""   
    vca = _getVCA(ctx)
    headers= ['Property', 'Value']
    table = []
    for property in properties:
        if isinstance(ctx.obj[property], basestring):
            table.append([property, (ctx.obj[property][:50]+'..') if len(ctx.obj[property])>50 else ctx.obj[property]])
        else:
            table.append([property, ctx.obj[property]])
    table.append(["session", 'active' if (vca and vca.vcloud_session) else 'inactive'])        
    sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)      
    print_table("Status:", 'status', headers, sorted_table, ctx.obj['json_output'])             
        
@cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[list | info]', type=click.Choice(['list', 'info']))
@click.option('-p', '--plan', default='', metavar='<plan>', help='Plan Id')
def plan(ctx, operation, plan):
    """Operations with Instances"""
    vca = _getVCA(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'list' == operation:
        headers = ["Plan Id", "Region", "Type"]
        plans = vca.get_plans()
        items = plans if plans else []
        table = [[item['id'], item['region'], item['name']] for item in items]
        print_table("Available plans for user '%s' in '%s' profile:" % (ctx.obj['user'], ctx.obj['profile']), 'plans', headers, table, ctx.obj['json_output'])
    elif 'info' == operation:
        print 'info about plan'
                
@cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[list | info]', type=click.Choice(['list', 'info']))
@click.option('-i', '--instance', default='', metavar='<instance>', help='Instance Id')
def instance(ctx, operation, instance):
    """Operations with Instances"""
    vca = _getVCA(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'list' == operation:
        headers = ["Instance Id", "Region", "Plan Id"]
        instances = vca.instances
        items = instances if instances else []
        table = [[item['id'], item['region'], item['planId']] for item in items]
        print_table("Available instances for user '%s' in '%s' profile:" % (ctx.obj['user'], ctx.obj['profile']), 'instances', headers, table, ctx.obj['json_output'])
    elif 'info' == operation:
        print_message("not implemented", ctx.obj['json_output'])

@cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[list | use | info]', type=click.Choice(['list', 'use', 'info']))
@click.option('-s', '--service', default='', metavar='<service>', help='Service Id')
@click.option('-o', '--org', default='', metavar='<org>', help='Organization Id')
def org(ctx, operation, service, org):
    """Operations with Organizations"""
    if '' == service: service = ctx.obj['service']
    if '' == org: org = ctx.obj['org']    
    vca = _getVCA(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'list' == operation:
        headers = ['Organization Id', "Selected"]
        table = ['']
        if 'ondemand' == ctx.obj['service_type']:
            if vca.vcloud_session and vca.vcloud_session.organization:
                instance = filter(lambda instance: instance['id'] == ctx.obj['instance'], vca.instances)[0]
                headers = ['Instance Id', 'Region', 'Organization Id', "Selected"]
                table = []
                table.append([instance['id'], instance['region'], vca.vcloud_session.organization.name, '*'])
        elif 'subscription' == ctx.obj['service_type']:
            if vca.services:
                headers = ["Service Id", "Type", "Region", "Organization Id", "Status", "Selected"]
                table = []
                for s in vca.services.get_Service():
                    for vdc in vca.get_vdc_references(s.serviceId):
                        selected = '*' if ctx.obj['org'] == vdc.name else ' '
                        table.append([s.serviceId, s.serviceType, s.region, vdc.name, vdc.status, selected])            
        elif 'vcd' == ctx.obj['service_type']:
            if vca.vcloud_session and vca.vcloud_session.organization:
                table = []
                table.append([vca.vcloud_session.organization.name, '*'])
        print_table("Available Organizations for '%s' profile:" % ctx.obj['profile'], 'orgs', headers, table, ctx.obj['json_output'])
    elif 'use' == operation:
        #this might be redundant with _getVCA()  
        result = False
        if 'ondemand' == ctx.obj['service_type']:
            print_message("Can't change organization, use the login command to select another organization, indicating the instance id", ctx.obj['json_output'])
            return
        elif 'subscription' == ctx.obj['service_type']:
            result = vca.login_to_org(service, org)
        elif 'vcd' == ctx.obj['service_type']:
            # print_message("Use the login command to select another organization, indicating the organization id", ctx.obj['json_output'])
            return
        if result:
            if vca.org:            
                _save_property(ctx.obj['profile'], 'service', service)
                _save_property(ctx.obj['profile'], 'org', org)
                if vca.vcloud_session: 
                    _save_property(ctx.obj['profile'], 'org_url', vca.vcloud_session.org_url)
                    _save_property(ctx.obj['profile'], 'session_token', vca.vcloud_session.token)
                print_message("Using organization '%s' in profile '%s'" % (org, ctx.obj['profile']), ctx.obj['json_output'])
                print_org_details(ctx, vca)
                return
        print_error("Unable to select organization '%s' in profile '%s'" % (org, ctx.obj['profile']), ctx.obj['json_output'])
    elif 'info' == operation:
        if vca.vcloud_session:
            print_org_details(ctx, vca)
        else:
            print_message('no org selected', ctx.obj['json_output'])

# assumes the org (and service) has been previously selected
@cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[list | use | info]', type=click.Choice(['list', 'use', 'info']))
@click.option('-v', '--vdc', default='', metavar='<vdc>', help='Virtual Data Center Id')
def vdc(ctx, operation, vdc):       
    """Operations with Virtual Data Centers (vdc)"""
    if '' == vdc: vdc = ctx.obj['vdc']             
    vca = _getVCA_vcloud_session(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'list' == operation:
        headers = ['Virtual Data Center', "Selected"]
        table = ['', '']    
        if vca.vcloud_session and vca.vcloud_session.organization:
            headers = ['Virtual Data Center', "Selected"]
            links = vca.vcloud_session.organization.Link if vca.vcloud_session.organization else []
            if '' == vdc:
                vdcs = filter(lambda info: info.name and info.type_ == 'application/vnd.vmware.vcloud.vdc+xml', links)
                if len(vdcs) > 0: vdc = vdcs[0].get_name()
            table1 = [[details.get_name(), '*' if details.get_name() == vdc else ' '] for details in filter(lambda info: info.name and info.type_ == 'application/vnd.vmware.vcloud.vdc+xml', links)]
            table = sorted(table1, key=operator.itemgetter(0), reverse=False)                
            vdcs = filter(lambda info: info.name == vdc and info.type_ == 'application/vnd.vmware.vcloud.vdc+xml', links)
            if len(vdcs) > 0: _save_property(ctx.obj['profile'], 'vdc', vdc)
        print_table("Available Virtual Data Centers in org '%s' for '%s' profile:" % (ctx.obj['org'], ctx.obj['profile']), 'vdcs', headers, table, ctx.obj['json_output'])
    elif 'use' == operation:
        the_vdc = vca.get_vdc(vdc)
        if the_vdc:
            _save_property(ctx.obj['profile'], 'vdc', vdc)        
            if vca.vcloud_session: _save_property(ctx.obj['profile'], 'org_url', vca.vcloud_session.org_url)            
            print_message("Using vdc '%s' in profile '%s'" % (vdc, ctx.obj['profile']), ctx.obj['json_output'])
            print_vdc_details(ctx, the_vdc, vca.get_gateways(vdc))
            return
        print_error("Unable to select vdc '%s' in profile '%s'" % (vdc, ctx.obj['profile']), ctx.obj['json_output'])
    elif 'info' == operation:    
        the_vdc = vca.get_vdc(vdc)
        if the_vdc:
            print_vdc_details(ctx, the_vdc, vca.get_gateways(vdc))
            _save_property(ctx.obj['profile'], 'vdc', vdc)
            return
        print_error("Unable to select vdc '%s' in profile '%s'" % (vdc, ctx.obj['profile']), ctx.obj['json_output'])

# assumes the org (and service) and vdc been previously selected   
@cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[list | info | create | delete | power.on | power.off | deploy | undeploy | customize | insert | eject]', type=click.Choice(['list', 'info', 'create', 'delete', 'power.on', 'power.off', 'deploy', 'undeploy', 'customize', 'insert', 'eject']))
@click.option('-v', '--vdc', default='', metavar='<vdc>', help='Virtual Data Center Id')
@click.option('-a', '--vapp', default='', metavar='<vapp>', help='vApp name')
@click.option('-c', '--catalog', default='', metavar='<catalog>', help='catalog name')
@click.option('-t', '--template', default='', metavar='<template>', help='template name')
@click.option('-n', '--network', default='', metavar='<network>', help='Network name')
@click.option('-m', '--mode', default='POOL', metavar='[POOL, DHCP]', help='Network connection mode', type=click.Choice(['POOL', 'DHCP']))
@click.option('-V', '--vm', 'vm_name', default='', metavar='<vm>', help='VM name')
@click.option('-f', '--file', 'cust_file', default=None, metavar='<customization_file>', help='Guest OS Customization script file', type=click.File('r'))
@click.option('-e', '--media', default='', metavar='<media>', help='virtual media name (ISO)')
def vapp(ctx, operation, vdc, vapp, catalog, template, network, mode, vm_name, cust_file, media):
    """Operations with vApps"""
    if vdc == '': vdc = ctx.obj['vdc'] 
    vca = _getVCA_vcloud_session(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'list' == operation:
        headers = ['vApp', "VMs", "Status", "Deployed", "Description"]
        table = []    
        the_vdc = vca.get_vdc(vdc)
        if the_vdc:
            table1 = []
            for entity in the_vdc.get_ResourceEntities().ResourceEntity:
                if entity.type_ == 'application/vnd.vmware.vcloud.vApp+xml':
                    the_vapp = vca.get_vapp(the_vdc, entity.name)
                    vms = []
                    if the_vapp and the_vapp.me.Children:
                        for vm in the_vapp.me.Children.Vm:
                            vms.append(vm.name)
                        # virtualHardwareSection = filter(lambda section: section.__class__.__name__== "VirtualHardwareSection_Type", sections)[0]
                    table1.append([entity.name, vms, status[the_vapp.me.get_status()](), 'yes' if the_vapp.me.deployed else 'no', the_vapp.me.Description])                     
            table = sorted(table1, key=operator.itemgetter(0), reverse=False)                
        print_table("Available vApps in '%s' for '%s' profile:" % (vdc, ctx.obj['profile']), 'vapps', headers, table, ctx.obj['json_output'])
    elif 'create' == operation:
        print_message("creating vApp '%s' in VDC '%s' from template '%s' in catalog '%s'" % (vapp, vdc, template, catalog), ctx.obj['json_output'])
        task = vca.create_vapp(vdc, vapp, template, catalog, vm_name=vm_name)
        if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
        else: print_error("can't create the vApp", ctx.obj['json_output'])
        if '' != network:
            the_vdc = vca.get_vdc(vdc)        
            the_vapp = vca.get_vapp(the_vdc, vapp)
            print_message("disconnecting vApp from networks pre-defined in the template", ctx.obj['json_output'])
            task = the_vapp.disconnect_from_networks()
            if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
            else: print_error("can't disconnect vApp from networks", ctx.obj['json_output'])
            nets = filter(lambda n: n.name == network, vca.get_networks(vdc))
            if len(nets) == 1:
                print_message("connecting vApp to network '%s' with mode '%s'" % (network, mode), ctx.obj['json_output'])
                task = the_vapp.connect_to_network(nets[0].name, nets[0].href)
                if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
                else: print_error("can't connect the vApp to the network", ctx.obj['json_output'])
                print_message("connecting VMs to network '%s' with mode '%s'" % (network, mode), ctx.obj['json_output'])                
                task = the_vapp.connect_vms(nets[0].name, mode)
                if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
                else: print_error("can't connect the vApp to the network", ctx.obj['json_output'])
    elif 'delete' == operation:
        print "deleting vApp '%s' from VDC '%s'" % (vapp, vdc)
        task = vca.delete_vapp(vdc, vapp)
        if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
        else: print_error("can't delete vApp", ctx.obj['json_output'])
    elif 'deploy' == operation:
        print "deploying vApp '%s' to VDC '%s'" % (vapp, vdc)
        the_vdc = vca.get_vdc(vdc)        
        the_vapp = vca.get_vapp(the_vdc, vapp)
        task = the_vapp.deploy()
        if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
        else: print_error("can't deploy vApp", ctx.obj['json_output'])        
    elif 'undeploy' == operation:
        print "undeploying vApp '%s' from VDC '%s'" % (vapp, vdc)
        the_vdc = vca.get_vdc(vdc)        
        the_vapp = vca.get_vapp(the_vdc, vapp)
        task = the_vapp.undeploy()
        if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
        else: print_error("can't undeploy vApp", ctx.obj['json_output'])        
    elif 'customize' == operation:
        print "customizing VM '%s' in vApp '%s' in VDC '%s'" % (vm_name, vapp, vdc)
        the_vdc = vca.get_vdc(vdc)        
        the_vapp = vca.get_vapp(the_vdc, vapp)
        if the_vdc and the_vapp and cust_file:
            print_message("uploading customization script", ctx.obj['json_output'])
            task = the_vapp.customize_guest_os(vm_name, cust_file.read())
            if task: 
                display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
                print_message("deploying and starting the vApp", ctx.obj['json_output'])
                task = the_vapp.force_customization(vm_name)
                if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
                else: print_error("can't customize vApp", ctx.obj['json_output'])
            else: print_error("can't customize vApp", ctx.obj['json_output'])
    elif 'info' == operation or 'power.off' == operation or 'power.on' == operation or 'delete' == operation:
        the_vdc = vca.get_vdc(vdc)
        if the_vdc:
            the_vapp = vca.get_vapp(the_vdc, vapp)
            if the_vapp and the_vapp.me:
                if 'info' == operation:
                    print_vapp_details(ctx, the_vapp.me)
                else:
                    task = None
                    if 'power.on' == operation: task = the_vapp.poweron()
                    elif 'power.off' == operation: task = the_vapp.poweroff()
                    elif 'delete' == operation: task = the_vapp.delete()                    
                    if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
                    else: print_error("can't operate with the vApp", ctx.obj['json_output'])                                
                _save_property(ctx.obj['profile'], 'vdc', vdc)
            else:
                print_error("vApp '%s' not found" % vapp, ctx.obj['json_output'])
    elif 'insert' == operation or 'eject' == operation:
        the_vdc = vca.get_vdc(vdc)
        if the_vdc:
            the_vapp = vca.get_vapp(the_vdc, vapp)
            if the_vapp:
                the_media = vca.get_media(catalog, media)
                task = the_vapp.vm_media(vm_name, the_media, operation)
                if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
                else: print_error("can't insert or eject media", ctx.obj['json_output'])
    else:
        print_message('not implemented', ctx.obj['json_output'])
        
def statusn1():
    return "Could not be created"
def status0():
    return "Unresolved"
def status1():
    return "Resolved"
def status2():
    return "Deployed"
def status3():
    return "Suspended"
def status4():
    return "Powered on"
def status5():
    return "Waiting for user input"
def status6():
    return "Unknown state"
def status7():
    return "Unrecognized state"
def status8():
    return "Powered off"
def status9():
    return "Inconsistent state"
def status10():
    return "Children do not all have the same status"
def status11():
    return "Upload initiated, OVF descriptor pending"
def status12():
    return "Upload initiated, copying contents"
def status13():
    return "Upload initiated , disk contents pending"
def status14():
    return "Upload has been quarantined"
def status15():
    return "Upload quarantine period has expired"
status = {-1 : statusn1,
           0 : status0,
           1 : status1,
           2 : status2,
           3 : status3,
           4 : status4,
           5 : status5,
           6 : status6,
           7 : status7,
           8 : status8,
           9 : status9,
           10 : status10,
           11 : status11,
           12 : status12,
           13 : status13,
           14 : status14,
           15 : status15,
            }        
        
@cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[list]', type=click.Choice(['list']))
@click.option('-v', '--vdc', default='', metavar='<vdc>', help='Virtual Data Center Id')
@click.option('-a', '--vapp', default='', metavar='<vapp>', help='vApp name')
def vm(ctx, operation, vdc, vapp):
    """Operations with Virtual Machines (VMs)"""
    if vdc == '': vdc = ctx.obj['vdc'] 
    vca = _getVCA_vcloud_session(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'list' == operation:
        headers = ['VM', "vApp", "Status", "IPs", "Networks", "vCPUs", "Memory (GB)", "CD/DVD", "OS", "Owner"]
        table = []    
        the_vdc = vca.get_vdc(vdc)
        if the_vdc:
            table1 = []
            for entity in the_vdc.get_ResourceEntities().ResourceEntity:
                if entity.type_ == 'application/vnd.vmware.vcloud.vApp+xml':
                    if vapp != '' and vapp != entity.name:
                        continue
                    the_vapp = vca.get_vapp(the_vdc, entity.name)
                    #todo: add disk info
                    if not the_vapp or not the_vapp.me or not the_vapp.me.Children:
                        continue
                    for vm in the_vapp.me.Children.Vm:
                        owner = the_vapp.me.get_Owner().get_User().get_name()
                        vm_status = status[vm.get_status()]()
                        sections = vm.get_Section()
                        virtualHardwareSection = filter(lambda section: section.__class__.__name__== "VirtualHardwareSection_Type", sections)[0]
                        items = virtualHardwareSection.get_Item()
                        cpu = filter(lambda item: item.get_Description().get_valueOf_() == "Number of Virtual CPUs", items)[0]
                        cpu_capacity = cpu.get_ElementName().get_valueOf_().split(" virtual CPU(s)")[0]
                        memory = filter(lambda item: item.get_Description().get_valueOf_() == "Memory Size", items)[0]
                        memory_capacity = int(memory.get_ElementName().get_valueOf_().split(" MB of memory")[0]) / 1024
                        operatingSystemSection = filter(lambda section: section.__class__.__name__== "OperatingSystemSection_Type", sections)[0]
                        os = operatingSystemSection.get_Description().get_valueOf_()
                        ips = []
                        networks = []
                        cds = []
                        for item in items:
                            if item.Connection:
                                for c in item.Connection:
                                    networks.append(c.valueOf_)
                                    if c.anyAttributes_.get('{http://www.vmware.com/vcloud/v1.5}ipAddress'):                                                                 
                                        #print c.anyAttributes_.get('{http://www.vmware.com/vcloud/v1.5}ipAddress')
                                        ips.append(c.anyAttributes_.get('{http://www.vmware.com/vcloud/v1.5}ipAddress'))
                            elif item.HostResource and item.ResourceSubType and item.ResourceSubType.valueOf_ == 'vmware.cdrom.iso':
                                if len(item.HostResource[0].valueOf_)>0:
                                    cds.append(item.HostResource[0].valueOf_)
                        table1.append([vm.name, entity.name, vm_status, ips, networks, cpu_capacity, str(memory_capacity), cds, os, owner])
            table = sorted(table1, key=operator.itemgetter(0), reverse=False)                
        print_table("Available VMs in '%s' for '%s' profile:" % (vdc, ctx.obj['profile']), 'vms', headers, table, ctx.obj['json_output'])   
    else:
        print_message('not implemented', ctx.obj['json_output'])       
        
@cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[info | list | create | delete]', type=click.Choice(['info', 'list', 'create', 'delete']))
@click.option('-v', '--vdc', default='', metavar='<vdc>', help='Virtual Data Center Id')
@click.option('-c', '--catalog', 'catalog_name', default='', metavar='<catalog>', help='Catalog Name')
@click.option('-d', '--description', default='', metavar='<description>', help='Catalog Description')
def catalog(ctx, operation, vdc, catalog_name, description):
    """Operations with Catalogs"""
    if vdc == '': vdc = ctx.obj['vdc']     
    # vca = _getVCA(ctx)
    vca = _getVCA_vcloud_session(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'create' == operation:
        task = vca.create_catalog(catalog_name, description)
        if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
        else: print_error("can't create the catalog", ctx.obj['json_output'])
    elif 'delete' == operation:
        result = vca.delete_catalog(catalog_name)
        if result:
            print_message('catalog deleted', ctx.obj['json_output'])
        else:
            print_error("can't delete the catalog", ctx.obj['json_output'])
    elif 'list':
        catalogs = vca.get_catalogs()
        print_catalogs(ctx, catalogs)
    else:
        print_message('not implemented', ctx.obj['json_output'])


#todo: default operation here is info instead of list, fixme
#todo: consider a specific edge, a vdc can have more than one
@cli.command()
@click.pass_context
@click.argument('operation', default='info', metavar='[info | add | delete]', type=click.Choice(['info', 'add', 'delete']))
@click.option('--type', 'rule_type', default='DNAT', metavar='<type>', help='Rule type', type=click.Choice(['DNAT', 'SNAT']))
@click.option('--original_ip', default='', metavar='<ip>', help='Original IP')
@click.option('--original_port', default='any', metavar='<port>', help='Original Port')
@click.option('--translated_ip', default='', metavar='<ip>', help='Translated IP')
@click.option('--translated_port', default='any', metavar='<port>', help='Translated Port')
@click.option('--protocol', default='any', metavar='<protocol>', help='Protocol', type=click.Choice(['any', 'tcp', 'udp']))
@click.option('-f', '--file', 'nat_rules_file', default=None, metavar='<nat_rules_file>', help='NAT rules file', type=click.File('r'))
@click.option('--all', is_flag=True)
def nat(ctx, operation, rule_type, original_ip, original_port, translated_ip, translated_port, protocol, nat_rules_file, all):
    """Operations with Edge Gateway NAT Rules"""
    # vca = _getVCA(ctx)
    vca = _getVCA_vcloud_session(ctx)
    vdc = ctx.obj['vdc'] 
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    gateways = vca.get_gateways(vdc)
    if len(gateways) != 1:
        print_error('Gateway not found', ctx.obj['json_output'])
        return
    if 'info' == operation:
        rules = gateways[0].get_nat_rules()
        print_nat_rules(ctx, rules)
    elif 'add' == operation:
        if nat_rules_file:
            rules = yaml.load(nat_rules_file)
            if rules and rules[0]:
                nat_rules = rules[0].get('NAT_rules')
                for rule in nat_rules:
                    gateways[0].add_nat_rule(rule.get('type'), rule.get('original_ip'), rule.get('original_port'), rule.get('translated_ip'), rule.get('translated_port'), rule.get('protocol'))
        else:
            gateways[0].add_nat_rule(rule_type, original_ip, original_port, translated_ip, translated_port, protocol)
        task = gateways[0].save_services_configuration()
        if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
        else: print_error("can't operate with the edge gateway", ctx.obj['json_output'])
    elif 'delete':
        found_rule = False
        if all:
            gateways[0].del_all_nat_rules()
            found_rule = True
        else:
            found_rule = gateways[0].del_nat_rule(rule_type, original_ip, original_port, translated_ip, translated_port, protocol)
        if found_rule:
            task = gateways[0].save_services_configuration()
            if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
            else: print_error("can't operate with the edge gateway", ctx.obj['json_output'])        
        else: print_error("rule doesn't exist in edge gateway", ctx.obj['json_output'])        
    else:
        print_message('not implemented', ctx.obj['json_output'])

#todo: default operation here is info instead of list, fixme
#todo: consider a specific edge, a vdc can have more than one
@cli.command()
@click.pass_context
@click.argument('operation', default='info', metavar='[info | enable | disable]', type=click.Choice(['info', 'enable', 'disable']))
def firewall(ctx, operation):
    """Operations with Edge Gateway Firewall Rules"""
    # vca = _getVCA(ctx)
    vca = _getVCA_vcloud_session(ctx)
    vdc = ctx.obj['vdc'] 
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    gateways = vca.get_gateways(vdc)
    if len(gateways) != 1:
        print_error('Gateway not found', ctx.obj['json_output'])
        return
    if 'enable' == operation or 'disable' == operation:    
        gateways[0].enable_fw('enable'==operation)
        task = gateways[0].save_services_configuration()
        if task: display_progress(task, ctx.obj['json_output'], vca.vcloud_session.get_vcloud_headers())
        else: print_error("can't operate with the edge gateway", ctx.obj['json_output'])                                
        # gateway_name = gateways[0].get_name()
        # gateways = [vca.get_gateway(vdc, gateway_name)]
        # print_gateways(ctx, gateways)
    elif 'info' == operation:
        print_message('not implemented', ctx.obj['json_output'])                
    else:
        print_message('not implemented', ctx.obj['json_output'])

@cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[info | list | use]', type=click.Choice(['info', 'list', 'use']))
def network(ctx, operation):
    """Operations with Networks"""
    # vca = _getVCA(ctx)
    vca = _getVCA_vcloud_session(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'list' == operation:
        print_networks(ctx, vca.get_networks(ctx.obj['vdc']))
    elif 'use' == operation:
        print_message('not implemented', ctx.obj['json_output'])                
    else:
        print_message('not implemented', ctx.obj['json_output'])

# @cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[info | list | use]', type=click.Choice(['info', 'list', 'use']))
def template(ctx, operation):
    """Operations with ..."""
    # if vdc == '': vdc = ctx.obj['vdc'] 
    # vca = _getVCA(ctx)
    vca = _getVCA_vcloud_session(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'list' == operation:
        print_message('not implemented', ctx.obj['json_output'])                                
    elif 'use' == operation:
        print_message('not implemented', ctx.obj['json_output'])                        
    elif 'info' == operation:
        print_message('not implemented', ctx.obj['json_output'])                
    else:
        print_message('not implemented', ctx.obj['json_output'])
    # if vdc != '': _save_property(ctx.obj['profile'], 'vdc', vdc)
    
@cli.command()
@click.pass_context
@click.argument('operation', default=default_operation, metavar='[info | list | use]', type=click.Choice(['info', 'list', 'use']))
@click.option('-s', '--service', default='', metavar='<service>', help='Service Id')
@click.option('-d', '--org', default='', metavar='<org>', help='Organization Id')
@click.option('-v', '--vdc', default='', metavar='<vdc>', help='Virtual Data Center Id')
def gateway(ctx, operation, service, org, vdc):
    """Operations with Edge Gateway"""
    if service == '': service = ctx.obj['service']
    if org == '': org = ctx.obj['org']
    if vdc == '': vdc = ctx.obj['vdc']             
    # vca = _getVCA(ctx)
    vca = _getVCA_vcloud_session(ctx)
    if not vca:
        print_error('User not authenticated or token expired', ctx.obj['json_output'])
        return
    if 'list' == operation:
        gateways = vca.get_gateways(vdc)
        print_gateways(ctx, gateways)
    elif 'use' == operation or 'info' == operation:
        gateways = vca.get_gateways(vdc)
        if len(gateways) > 0:
            print_gateway_details(ctx, gateways[0])
    if service != '': _save_property(ctx.obj['profile'], 'service', service)
    if org != '': _save_property(ctx.obj['profile'], 'org', org)
    if vdc != '': _save_property(ctx.obj['profile'], 'vdc', vdc)      
    
@cli.command()
@click.pass_context
def example(ctx):
    """vCloud Air CLI Examples"""
    headers = ['Id', 'Example', "Command"]
    id = 0
    table = []
    id+=1; table.append([id, 'login to vCA On Demand', 
        'vca login email@company.com --password mypassword'])
    id+=1; table.append([id, 'login to a vCA On Demand instance', 
        'vca login email@company.com --password mypassword --instance c40ba6b4-c158-49fb-b164-5c66f90344fa'])        
    id+=1; table.append([id, 'login to vCA Subscription', 
        'vca login email@company.com --password mypassword --type subscription --host https://vchs.vmware.com --version 5.6'])
    id+=1; table.append([id, 'login to vCloud Director', 
        'vca login email@company.com --password mypassword --type vcd --host https://p1v21-vcd.vchs.vmware.com --version 5.6 --org MyOrganization'])
    id+=1; table.append([id, 'login with no SSL verification', 
        'vca --insecure login email@company.com --password mypassword'])
    id+=1; table.append([id, 'prompt user for password', 
        'vca login email@company.com'])        
    id+=1; table.append([id, 'show status', 
        'vca status'])    
    id+=1; table.append([id, 'logout', 
        'vca logout'])    
    id+=1; table.append([id, 'list organizations', 
        'vca org'])
    id+=1; table.append([id, 'select organization', 
        'vca org use --org MyOrg'])
    id+=1; table.append([id, 'select organization in subscription', 
        'vca org use --org MyOrg --service ServiceId'])        
    id+=1; table.append([id, 'show current organization', 
        'vca org info'])
    id+=1; table.append([id, 'select and show organization', 
        'vca org info --org MyOrg'])
    id+=1; table.append([id, 'show current organization in XML', 
        'vca --xml org info'])
    id+=1; table.append([id, 'show current organization in JSON', 
        'vca --json org info'])
    id+=1; table.append([id, 'list virtual data centers', 
        'vca vdc'])
    id+=1; table.append([id, 'select virtual data centers', 
        'vca vdc use --vdc VDC1'])
    id+=1; table.append([id, 'show virtual data center', 
        'vca vdc info'])
    id+=1; table.append([id, 'list catalogs', 
        'vca catalog'])
    id+=1; table.append([id, 'create catalog', 
        'vca catalog create --catalog mycatalog'])
    id+=1; table.append([id, 'delete catalog', 
        'vca catalog delete --catalog mycatalog'])
    id+=1; table.append([id, 'list networks', 
        'vca network'])        
    id+=1; table.append([id, 'list vapps', 
        'vca vapp'])
    id+=1; table.append([id, 'create vapp', 
        'vca vapp create -a coreos2 -V coreos2 -c default-catalog -t coreos_template -n default-routed-network -m POOL'])        
    id+=1; table.append([id, 'delete vapp', 
        'vca vapp delete -a coreos2'])        
    id+=1; table.append([id, 'show vapp details in XML', 
        'vca -x vapp info -a coreos2'])        
    id+=1; table.append([id, 'deploy vapp', 
        'vca vapp deploy --vapp ubu'])                        
    id+=1; table.append([id, 'undeploy vapp', 
        'vca vapp undeploy --vapp ubu'])                
    id+=1; table.append([id, 'customize vapp vm', 
        'vca vapp customize --vapp ubu --vm ubu --file add_public_ssh_key.sh'])                        
    id+=1; table.append([id, 'insert ISO to vapp vm', 
        'vca vapp insert --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso'])                        
    id+=1; table.append([id, 'eject ISO from vapp vm', 
        'vca vapp eject --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso'])                        
    id+=1; table.append([id, 'list vms', 
        'vca vm'])
    id+=1; table.append([id, 'list vms in a vapp', 
        'vca vm -a ubu'])        
    id+=1; table.append([id, 'list vms in JSON format', 
        'vca -j vm'])
    id+=1; table.append([id, 'retrieve the IP of a vm', 
        "IP=`vca -j vm -a ubu | jq '.vms[0].IPs[0]'` && echo $IP"])
    id+=1; table.append([id, 'list edge gateway NAT rules', 
        'vca nat'])
    id+=1; table.append([id, 'add edge gateway DNAT rule',
        "vca nat add --type DNAT --original_ip 107.189.93.162 --original_port 22 --translated_ip 192.168.109.2 --translated_port 22 --protocol tcp"])
    id+=1; table.append([id, 'add edge gateway SNAT rule',
        "vca nat add --type SNAT --original_ip 192.168.109.0/24 --translated_ip 107.189.93.162"])
    id+=1; table.append([id, 'add edge gateway rules from file',
        "vca nat add --file natrules.yaml"])        
    id+=1; table.append([id, 'delete edge gateway NAT rule',
        "vca nat delete --type DNAT --original_ip 107.189.93.162 --original_port 22 --translated_ip 192.168.109.4 --translated_port 22 --protocol tcp"])
    id+=1; table.append([id, 'delete all edge gateway NAT rules',
        "vca nat delete --all"])
    id+=1; table.append([id, 'show the REST calls in the command', 
        'vca --debug vm'])
    id+=1; table.append([id, 'show version', 
        'vca --version'])
    id+=1; table.append([id, 'show help', 
        'vca --help'])
    id+=1; table.append([id, 'show command help', 
        'vca <command> --help'])

    print_table('vca-cli usage examples:', 'examples', headers, table, ctx.obj['json_output'])   
        
def _getVCA(ctx):
    # for k, v in ctx.obj.iteritems(): print k, "==>", v
    if ctx.obj['token'] == None:
        return None
    vca = VCA(ctx.obj['host'], ctx.obj['user'], ctx.obj['service_type'], ctx.obj['service_version'], ctx.obj['verify'])        
    if vca.login(token=ctx.obj['token'], org=ctx.obj['org'], org_url=ctx.obj['org_url']):
        if 'ondemand' == ctx.obj['service_type']:
            if ctx.obj['instance'] and ctx.obj['session_token']:
                result = vca.login_to_instance(ctx.obj['instance'], None, ctx.obj['session_token'], ctx.obj['org_url'])
                if result:
                    ctx.obj['session_uri'] = vca.vcloud_session.url
                    _save_property(ctx.obj['profile'], 'session_uri', ctx.obj['session_uri'])      
                    ctx.obj['verify'] = vca.verify
                    _save_property(ctx.obj['profile'], 'verify', ctx.obj['verify'])                          
                else:
                    return None
        elif 'subscription' == ctx.obj['service_type']:
            if ctx.obj['service'] and ctx.obj['session_token']:
                result = vca.login_to_org(ctx.obj['service'], ctx.obj['org'])
                if result:
                    ctx.obj['session_uri'] = vca.vcloud_session.url
                    _save_property(ctx.obj['profile'], 'session_uri', ctx.obj['session_uri'])      
                    ctx.obj['verify'] = vca.verify
                    _save_property(ctx.obj['profile'], 'verify', ctx.obj['verify'])                          
                else:
                    return None
        return vca
    else:
        return None

def _getVCA_vcloud_session(ctx):
    # for k, v in ctx.obj.iteritems(): print k, "-->", v
    if ctx.obj['org_url'] == None or ctx.obj['org'] == None or ctx.obj['session_uri'] == None:
        return _getVCA(ctx)
    vca = VCA(ctx.obj['host'], ctx.obj['user'], ctx.obj['service_type'], ctx.obj['service_version'], ctx.obj['verify'])                
    if 'ondemand' == ctx.obj['service_type'] or 'subscription' == ctx.obj['service_type']:
        vcloud_session = VCS(ctx.obj['session_uri'], ctx.obj['user'], ctx.obj['org'], ctx.obj['instance'], ctx.obj['org_url'], ctx.obj['org_url'], ctx.obj['service_version'], ctx.obj['verify'])
        result = vcloud_session.login(token=ctx.obj['session_token'])
        if result:
            vca.vcloud_session = vcloud_session
            return vca
    else:
        return _getVCA(ctx)
        
def print_table(msg, obj, headers, table, json_output):    
    if json_output:
        data = [dict(zip(headers, row)) for row in table]
        print json.dumps({"Errorcode" : "0" , "Details" : msg, obj : data}, sort_keys=True, indent=4, separators=(',', ': '))
    else:
        click.echo(click.style(msg, fg='blue'))
        print tabulate(table, headers = headers, tablefmt="orgtbl")
        
def print_message(msg, json_output):
    if json_output:
        json_msg = {"Returncode" : "1", "Details" : msg}        
        print json.dumps(json_msg, sort_keys=True, indent=4, separators=(',', ': '))
    else:
        click.secho(msg, fg='blue')
    
def print_error(msg, json_output):    
    if json_output:
        json_msg = {"Errorcode" : "1", "Details" : msg}
        print json.dumps(json_msg, sort_keys=True, indent=4, separators=(',', ': '))
    else:
        click.secho(msg, fg='red')
        
def print_json(obj, headers, table):
    data = [dict(zip(headers, row)) for row in table]
    print json.dumps({"Errorcode" : "0" , obj : data}, sort_keys=True, indent=4, separators=(',', ': '))

def remove_task_unwanted_keys(task_dict):
    removed_keys = ["expiryTime", "cancelRequested", "id", "name", "operation",
                   "operationName", "serviceNamespace", "type", "xmlns",
                   "xmlns:xsi", "xsi:schemaLocation", "Details",
                   "Organization", "Owner", "User"]
    for removed_key in removed_keys:
        for key in task_dict["Task"]:
            if removed_key in key:
                del task_dict["Task"][key]
                break        
        
def task_json(task_xml):
    task_dict = xmltodict.parse(task_xml)
    remove_task_unwanted_keys(task_dict)
    # add error message (0 means no error and 1 means error)
    task_dict["Errorcode"] = "0"
    return json.dumps(task_dict, sort_keys=True, indent=4, separators=(',', ': '))

def task_table(task_xml):
    task_dict = xmltodict.parse(task_xml)
    remove_task_unwanted_keys(task_dict)
    # modify link so that it can be printed on the table
    for key in task_dict["Task"]:
        if "Link" in key:
            rel = [task_dict["Task"][key][link_key] for link_key in task_dict["Task"][key] if "rel" in link_key][0]
            href = [task_dict["Task"][key][link_key] for link_key in task_dict["Task"][key] if "href" in link_key][0]
            task_dict["Task"][rel] = href
            del task_dict["Task"][key]
    # add error message (0 means no error and 1 means error)
    table = task_dict["Task"].items()
    return tabulate(table, tablefmt="grid")        
        
def display_progress(task, json, headers):
    progress = task.get_Progress()
    status = task.get_status()
    rnd = 0
    while status != "success":
        if status == "error":
            error = task.get_Error()
            print_error(CommonUtils.convertPythonObjToStr(error, name = "Error"), json)
            return
        else:
            # some task doesn't not report progress
            if progress:
                sys.stdout.write("\rprogress : ["+"*"*int(progress)+" "*(100-int(progress-1))+"] "+str(progress)+" %")
            else:
                sys.stdout.write("\rprogress : ")
                if rnd % 4 == 0:
                    sys.stdout.write("["+"*"*25+" "*75+"]")
                elif rnd % 4 == 1:
                    sys.stdout.write("["+" "*25+"*"*25+" "*50+"]")
                elif rnd % 4 == 2:
                    sys.stdout.write("["+" "*50+"*"*25+" "*25+"]")
                elif rnd % 4 == 3:
                    sys.stdout.write("["+" "*75+"*"*25+"]")
                rnd += 1
            sys.stdout.flush()
            time.sleep(1)
            response = requests.get(task.get_href(), headers = headers)
            task = taskType.parseString(response.content, True)
            progress = task.get_Progress()
            status = task.get_status()
    sys.stdout.write("\r" + " "*120)
    sys.stdout.flush()
    if json:
        sys.stdout.write("\r" + task_json(response.content) + '\n')
    else:
        sys.stdout.write("\r" + task_table(response.content) + '\n')
    sys.stdout.flush()        
    
def print_org_details(ctx, vca):
    if ctx.obj['xml_output']:
        vca.vcloud_session.organization.export(sys.stdout, 0)
        return
    headers = ["Type", "Name"]
    links = vca.vcloud_session.organization.Link if vca.vcloud_session.organization else []
    org_name = vca.vcloud_session.organization.name if vca.vcloud_session.organization else []
    #todo: review filter/lambda below
    table = [[details.get_type().split('.')[-1].split('+')[0], details.get_name()] for details in filter(lambda info: info.name, links)]
    sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)        
    print_table("Details for org '%s':" % org_name, 'orgs', headers, sorted_table, ctx.obj['json_output'])     
    
def print_vdc_details(ctx, vdc, gateways):     
    if ctx.obj['xml_output']:
        vdc.export(sys.stdout, 0)
        for gateway in gateways: print_gateway_details(ctx, gateway)
        return       
    headers = ['Type', 'Name']
    table = []
    for entity in vdc.get_ResourceEntities().ResourceEntity:
        table.append([entity.type_.split('.')[-1].split('+')[0], entity.name])
    for entity in vdc.get_AvailableNetworks().Network:
        table.append([entity.type_.split('.')[-1].split('+')[0], entity.name])
    for gateway in gateways:
        table.append(['edge gateway', gateway.get_name()])
    sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)        
    print_table("Virtual Data Center '%s' for '%s' profile; details:" % (vdc.name, ctx.obj['profile']), 'vdc', headers, sorted_table, ctx.obj['json_output'])
                
    headers = ['Resource', 'Allocated', 'Limit', 'Reserved', 'Used', 'Overhead']
    table = []
    computeCapacity = vdc.get_ComputeCapacity()
    cpu = computeCapacity.get_Cpu()
    memory = computeCapacity.get_Memory()
    # storageCapacity = vca.vdc.get_StorageCapacity()
    table.append(['CPU (%s)' % cpu.get_Units(), cpu.get_Allocated(), cpu.get_Limit(), cpu.get_Reserved(), cpu.get_Used(), cpu.get_Overhead()])
    table.append(['Memory (%s)' % memory.get_Units(), memory.get_Allocated(), memory.get_Limit(), memory.get_Reserved(), memory.get_Used(), memory.get_Overhead()])
    sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)        
    print_table("Compute capacity:", 'compute', headers, sorted_table, ctx.obj['json_output'])
    
    print_gateways(ctx, gateways)
        
def print_gateways(ctx, gateways):
    if ctx.obj['xml_output']:
        for gateway in gateways: gateway.me.export(sys.stdout, 0)
        return
    #todo add VPN and LB services
    headers = ['Name', 'External IPs', 'DHCP Service', 'Firewall Service', 'NAT Service', 'Internal Networks']
    table = []
    for gateway in gateways:
        interfaces = gateway.get_interfaces('internal')
        interface_table = []
        for interface in interfaces: interface_table.append(interface.get_Name())
        table.append([gateway.get_name(), gateway.get_public_ips(), 
        'On' if gateway.is_dhcp_enabled() else 'Off', 
        'On' if gateway.is_fw_enabled() else 'Off', 
        'On' if gateway.is_nat_enabled() else 'Off', 
        interface_table])
    # sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)
    print_table("Edge Gateways:", 'gateways', headers, table, ctx.obj['json_output'])                
        
def print_gateway_details(ctx, gateway):
    if ctx.obj['xml_output']:
        gateway.me.export(sys.stdout, 0)
        return
    print_message("not implemented", ctx.obj['json_output'])
    return
    headers = ['Property', 'Value']
    table = []
    table.append(['Name', gateway.me.name])
    # headers = ['Type', 'Name']
    # table = []
    # for entity in vdc.get_ResourceEntities().ResourceEntity:
    #     table.append([entity.type_.split('.')[-1].split('+')[0], entity.name])
    # for entity in vdc.get_AvailableNetworks().Network:
    #     table.append([entity.type_.split('.')[-1].split('+')[0], entity.name])
    # for gateway in gateways:
    #     table.append(['edge gateway', gateway.name])
    # sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)
    print_table("Gateway '%s' details:" % (gateway.me.name), 'gateway', headers, table, ctx.obj['json_output'])
    
def print_networks(ctx, item_list):
    if ctx.obj['xml_output']:
        for item in item_list: item.export(sys.stdout, 0)
        return
    headers = ['Name', 'Status', 'DHCP Service', 'IP Range']
    table = []
    for item in item_list:
        table.append([item.get_name(), '', '', ''])
    sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)
    print_table("Networks available in Virtual Data Center '%s':" % (ctx.obj['vdc']), 'networks', headers, sorted_table, ctx.obj['json_output'])        
    
def print_vapp_details(ctx, vapp):            
    if ctx.obj['xml_output']:
        vapp.export(sys.stdout, 0)
        return
    headers = []
    sorted_table = []
    print_table("Details for vApp '%s':" % vapp.name, 'vapp', headers, sorted_table, ctx.obj['json_output'])  
    
def print_nat_rules(ctx, natRules):
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
        print_message("No NAT rules found in this gateway", ctx.obj['json_output']) 
        
def print_catalogs(ctx, catalogs):
    result = []
    for catalog in catalogs:
        if catalog.CatalogItems and catalog.CatalogItems.CatalogItem:
            for item in catalog.CatalogItems.CatalogItem:
                result.append([catalog.name, item.name])
        else:
            result.append([catalog.name, ''])
    if result:
        headers = ["Catalog", "Item"]
        sorted_table = sorted(result, key=operator.itemgetter(0), reverse=False)
        print_table("Catalogs and items:", 'catalogs', headers, sorted_table, ctx.obj['json_output'])  
    else:
        print_message("No catalogs found in this organization", ctx.obj['json_output'])         
    
if __name__ == '__main__':
    cli(obj={})
