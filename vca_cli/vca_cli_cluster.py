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
import operator
from pyvcloud.cluster import Cluster
from pyvcloud.task import Task
import sys
from vca_cli import cli
from vca_cli import default_operation
from vca_cli import utils


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | create | delete]',
                type=click.Choice(['list', 'info', 'create',
                                   'delete']))
@click.option('-c', '--name', 'cluster_name', default='',
              metavar='<cluster-name>', help='Cluster Name')
@click.option('-i', '--id', 'cluster_id', default='',
              metavar='<cluster-id>', help='Cluster Id')
@click.option('-N', '--nodes', 'node_count', default=2,
              metavar='<nodes>', help='Number of nodes to create')
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-n', '--network', 'network_name', default='',
              metavar='<network>', help='Network name')
def cluster(cmd_proc, operation, cluster_name, cluster_id, node_count, vdc,
            network_name):
    """Operations with Container Service Extension"""
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
    if cmd_proc.vca.vcloud_session and \
       cmd_proc.vca.vcloud_session.organization:
        cse = Cluster(session=cmd_proc.vca.vcloud_session,
                      verify=cmd_proc.verify, log=cmd_proc.vca.log)
        if 'list' == operation:
            headers = ['Name', 'Id', 'Status', 'Leader IP', 'Masters', 'Nodes']
            table1 = []
            try:
                clusters = cse.get_clusters()
            except Exception:
                utils.print_error("can't get list of clusters", cmd_proc, cse)
                sys.exit(1)
            n = 1
            for cluster in clusters:
                cluster['name'] = 'k8s-cluster-%s' % n
                n += 1
                table1.append([cluster['name'],
                               cluster['cluster_id'],
                               cluster['status'],
                               cluster['leader_endpoint'],
                               len(cluster['master_nodes']),
                               len(cluster['nodes']),
                               ])
            table = sorted(table1, key=operator.itemgetter(0), reverse=False)
            utils.print_table(
                "Available clusters in VDC '%s', profile '%s':" %
                (vdc, cmd_proc.profile),
                headers, table, cmd_proc)
        elif 'create' == operation:
            utils.print_message("creating cluster '%s'" %
                                (cluster_name))
            try:
                r = cse.create_cluster(vdc, network_name,
                                       cluster_name, node_count)
                t = Task(session=cmd_proc.vca.vcloud_session,
                         verify=cmd_proc.verify,
                         log=cmd_proc.vca.log)
                task = t.get_task(r['task_id'])
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            except Exception:
                utils.print_error("can't create cluster", cmd_proc, cse)
                sys.exit(1)
        elif 'delete' == operation:
            utils.print_message("deleting cluster with id '%s'" %
                                (cluster_id))
            try:
                r = cse.delete_cluster(cluster_id)
                t = Task(session=cmd_proc.vca.vcloud_session,
                         verify=cmd_proc.verify,
                         log=cmd_proc.vca.log)
                task = t.get_task(r['task_id'])
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            except Exception:
                utils.print_error("can't delete cluster", cmd_proc, cse)
                sys.exit(1)
        else:
            utils.print_error('not implemented', cmd_proc)
            sys.exit(1)
    cmd_proc.save_current_config()
