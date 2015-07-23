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
from vca_cli import cli, utils


@cli.command()
@click.pass_context
def example(ctx):
    """vCloud Air CLI Examples"""
    headers = ['Id', 'Example', 'Flavor', 'Command']
    example_id = 0
    table = []
    example_id += 1
    table.append([example_id, 'login to service', 'vCA',
                  'vca login email@company.com --password ****'])
    example_id += 1
    table.append([example_id, 'login to an instance', 'vCA',
                  'vca login email@company.com --password ****'
                  ' --instance c40ba6b4-c158-49fb-b164-5c66f90344fa'])
    example_id += 1
    table.append([example_id, 'login to a virtual data center', 'vCA',
                  'vca login email@company.com --password ****'
                  ' --instance c40ba6b4-c158-49fb-b164-5c66f90344fa'
                  ' --vdc VDC1'])
    example_id += 1
    table.append([example_id, 'login to service', 'vCHS',
                  'vca login email@company.com --password ****'
                  ' --host vchs.vmware.com --version 5.6'])
    example_id += 1
    table.append([example_id, 'login to an instance', 'vCHS',
                  'vca login email@company.com --password ****'
                  ' --host vchs.vmware.com --version 5.6'
                  ' --instance 55-234 --org MyOrg'])
    example_id += 1
    table.append([example_id, 'login to a virtual data center', 'vCHS',
                  'vca login email@company.com --password ****'
                  ' --host vchs.vmware.com --version 5.6'
                  ' --instance 55-234 --org MyOrg --vdc MyVDC'])
    example_id += 1
    table.append([example_id, 'login to vCloud Director', 'Standalone',
                  'vca login email@company.com --password ****'
                  ' --host myvcloud.company.com --version 5.5 --org MyOrg'])
    example_id += 1
    table.append([example_id, 'login to vCloud Director and VDC',
                  'Standalone',
                  'vca login email@company.com --password ****'
                  ' --host myvcloud.company.com --version 5.5 --org MyOrg'
                  ' --vdc MyVDC'])
    example_id += 1
    table.append([example_id, 'list available instances', 'vCA, vCHS',
                  'vca instance'])
    example_id += 1
    table.append([example_id, 'show details of instance', 'vCA, vCHS',
                  'vca instance info --instance '
                  'c40ba6b4-c158-49fb-b164-5c66f90344fa'])
    example_id += 1
    table.append([example_id, 'select an instance', 'vCA',
                  'vca instance use --instance '
                  'c40ba6b4-c158-49fb-b164-5c66f90344fa'])
    example_id += 1
    table.append([example_id, 'select an instance and VDC', 'vCA',
                  'vca instance use --instance '
                  'c40ba6b4-c158-49fb-b164-5c66f90344fa '
                  '--vdc MyVDC'])
    example_id += 1
    table.append([example_id, 'select an instance', 'vCHS',
                  'vca instance use --instance '
                  'M684216431-4470 --org M684216431-4470'])
    example_id += 1
    table.append([example_id, 'list organizations', 'All',
                  'vca org'])
    example_id += 1
    table.append([example_id, 'show organization details', 'All',
                  'vca org info'])
    example_id += 1
    table.append([example_id, 'select an organization', 'vCHS',
                  'vca org use --instance 55-234 --org MyOrg '])
    example_id += 1
    table.append([example_id, 'show status', 'All',
                  'vca status'])
    example_id += 1
    table.append([example_id, 'show status and password', 'All',
                  'vca status --show-password'])
    example_id += 1
    table.append([example_id, 'list profiles', 'All',
                  'vca profile'])
    example_id += 1
    table.append([example_id, 'switch to a profile', 'All',
                  'vca --profile p1 <command>'])
    example_id += 1
    table.append([example_id, 'send debug to $TMPDIR/pyvcloud.log', 'All',
                  'vca --debug vm'])
    example_id += 1
    table.append([example_id, 'show version', 'All',
                  'vca --version'])
    example_id += 1
    table.append([example_id, 'show general help', 'All',
                  'vca --help'])
    example_id += 1
    table.append([example_id, 'show command help', 'All',
                  'vca <command> --help'])
    utils.print_table('vca-cli usage examples:',
                      headers, table)
