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
    headers = ['Id', 'Example', "Command"]
    example_id = 0
    table = []
    example_id += 1
    table.append([example_id, 'login to vCA',
                  'vca login email@company.com --password mypassword'])
    example_id += 1
    table.append([example_id, 'login to a vCA instance',
                  'vca login email@company.com --password mypassword'
                  ' --instance c40ba6b4-c158-49fb-b164-5c66f90344fa'])
    example_id += 1
    table.append([example_id, 'login to a vCA virtual data center',
                  'vca login email@company.com --password mypassword'
                  ' --instance c40ba6b4-c158-49fb-b164-5c66f90344fa'
                  ' --vdc VDC1'])
    example_id += 1
    table.append([example_id, 'login to vCA (vCHS)',
                  'vca login email@company.com --password mypassword'
                  ' --host vchs.vmware.com --version 5.6'])
    example_id += 1
    table.append([example_id, 'login to vCA (vCHS) instance',
                  'vca login email@company.com --password mypassword'
                  ' --host vchs.vmware.com --version 5.6'
                  ' --instance 55-234 --org MyOrg'])
    example_id += 1
    table.append([example_id, 'login to vCA (vCHS) virtual data center',
                  'vca login email@company.com --password mypassword'
                  ' --host vchs.vmware.com --version 5.6'
                  ' --instance 55-234 --org MyOrg --vdc MyVDC'])
    example_id += 1
    table.append([example_id, 'login to vCloud Director',
                  'vca login email@company.com --password mypassword'
                  ' --host myvcloud.company.com --version 5.5 --org MyOrg'])
    example_id += 1
    table.append([example_id, 'login to vCloud Director and VDC',
                  'vca login email@company.com --password mypassword'
                  ' --host myvcloud.company.com --version 5.5 --org MyOrg'
                  ' --vdc MyVDC'])
    example_id += 1
    table.append([example_id, 'show status',
                  'vca status'])
    example_id += 1
    table.append([example_id, 'show status and password',
                  'vca status --show-password'])
    example_id += 1
    table.append([example_id, 'show profiles',
                  'vca profile'])
    example_id += 1
    table.append([example_id, 'send debug to $TMPDIR/pyvcloud.log',
                  'vca --debug vm'])
    example_id += 1
    table.append([example_id, 'show version',
                  'vca --version'])
    example_id += 1
    table.append([example_id, 'show help',
                  'vca --help'])
    example_id += 1
    table.append([example_id, 'show command help',
                  'vca <command> --help'])
    utils.print_table('vca-cli usage examples:',
                      headers, table)
