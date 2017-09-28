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
from os.path import expanduser
from os.path import join
from pyvcloud.vcd.cluster import Cluster
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import abort_if_false
from vcd_cli.vcd import vcd
import yaml


@vcd.group(short_help='manage clusters')
@click.pass_context
def cluster(ctx):
    """Work with kubernetes clusters in vCloud Director.

\b
    Examples
        vcd cluster list
            Get list of kubernetes clusters in current virtual datacenter.
\b
        vcd cluster create dev-cluster
            Create a kubernetes cluster in current virtual datacenter.
\b
        vcd cluster create prod-cluster --nodes 4
            Create a kubernetes cluster with 4 worker nodes.
\b
        vcd cluster delete dev-cluster
            Delete a kubernetes cluster by name.
\b
        vcd cluster create c1 --nodes 0
            Create a single node kubernetes cluster for dev/test.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
            if not ctx.obj['profiles'].get('vdc_in_use') or \
               not ctx.obj['profiles'].get('vdc_href'):
                raise Exception('select a virtual datacenter')
        except Exception as e:
            stderr(e, ctx)


@cluster.command(short_help='list clusters')
@click.pass_context
def list(ctx):
    try:
        client = ctx.obj['client']
        cluster = Cluster(client)
        result = []
        clusters = cluster.get_clusters()
        for c in clusters:
            result.append({'name': c['name'],
                           'IP master': c['leader_endpoint'],
                           'nodes': len(c['nodes']),
                           'vdc': c['vdc_name']
                           })
        stdout(result, ctx, show_id=True)
    except Exception as e:
        stderr(e, ctx)


@cluster.command(short_help='create cluster')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-N',
              '--nodes',
              'node_count',
              required=False,
              default=2,
              metavar='<nodes>',
              help='Number of nodes to create')
@click.option('-n',
              '--network',
              'network_name',
              default=None,
              required=False,
              metavar='<network>',
              help='Network name')
def create(ctx, name, node_count, network_name):
    try:
        client = ctx.obj['client']
        cluster = Cluster(client)
        result = cluster.create_cluster(
                    ctx.obj['profiles'].get('vdc_in_use'),
                    network_name,
                    name,
                    node_count)
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@cluster.command(short_help='delete cluster')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to delete the cluster?')
def delete(ctx, name):
    try:
        client = ctx.obj['client']
        cluster = Cluster(client)
        result = cluster.delete_cluster(name)
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@cluster.command(short_help='get cluster config')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def config(ctx, name):
    try:
        client = ctx.obj['client']
        cluster = Cluster(client)
        click.secho(cluster.get_config(name))
    except Exception as e:
        stderr(e, ctx)


@cluster.command('save-config')
@click.pass_context
def save_config(ctx):
    try:
        f = join(expanduser('~'), '.kube/config')
        stream = open(f, 'r')
        docs = yaml.load_all(stream)
        for doc in docs:
            for k, v in doc.items():
                if k == 'contexts':
                    for c in v:
                        print(c['name'])
                        print('  cluster: %s' % c['context']['cluster'])
                        print('  user:    %s' % c['context']['user'])
                # elif k == 'clusters':
                #     for cluster in v:
                #         print(cluster['name'], cluster['cluster']['server'])
                # elif k == 'users':
                #     for user in v:
                #         print(user['name'], user['user'])

    except Exception as e:
        stderr(e, ctx)
