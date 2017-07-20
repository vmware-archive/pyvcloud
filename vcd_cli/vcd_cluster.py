# vCloud CLI 0.1
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
from vcd_cli import as_metavar
from vcd_cli import cli
from vcd_cli import OPERATIONS



@cli.command()
@click.pass_context
@click.argument('operation',
                default=None,
                type=click.Choice(OPERATIONS),
                metavar=as_metavar(OPERATIONS)
                )
@click.argument('name',
                metavar='[name]',
                required=False)
@click.option('-N',
              '--nodes',
              'node_count',
              default=2,
              metavar='<nodes>',
              help='Number of nodes to create')
@click.option('-v',
              '--vdc',
              'vdc_name',
              default=None,
              metavar='<vdc>',
              help='Virtual Data Center Name')
@click.option('-n',
              '--network',
              'network_name',
              default=None,
              metavar='<network>',
              help='Network name')
def cluster(ctx, operation, name, node_count,
            vdc_name, network_name):
    """Operations with Container Service Extension"""
    print('cluster %s %s' % (operation, name))
