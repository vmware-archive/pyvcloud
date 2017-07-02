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
@click.option('-n', '--name', 'cluster_name', default='',
              metavar='<cluster-name>', help='Cluster Name')
@click.option('-i', '--id', 'cluster_id', default='',
              metavar='<cluster-id>', help='Cluster Id')
@click.option('-w', '--workers', 'worker_count', default=2,
              metavar='<workers>', help='Number of worker nodes to create')
def cluster(cmd_proc, operation, cluster_name, cluster_id, worker_count):
    """Operations with Container Service Extension"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if cmd_proc.vca.vcloud_session and \
       cmd_proc.vca.vcloud_session.organization:
        cse = Cluster(session=cmd_proc.vca.vcloud_session,
                      verify=cmd_proc.verify, log=cmd_proc.vca.log)
        if 'list' == operation:
            headers = ['Name', "Id", "Masters", "Nodes", "VMs"]
            table1 = []
            clusters = cse.get_clusters()
            for cluster in clusters:
                names = ''
                for mn in cluster['master_nodes']:
                    names += ' ' + mn['cse.node.name']
                for wn in cluster['worker_nodes']:
                    names += ' ' + wn['cse.node.name']
                table1.append([cluster['name'], cluster['id'],
                              len(cluster['master_nodes']),
                              len(cluster['worker_nodes']),
                              names.strip()])
            table = sorted(table1, key=operator.itemgetter(0), reverse=False)
            utils.print_table(
                "Available clusters in org '%s', profile '%s':" %
                (cmd_proc.vca.org, cmd_proc.profile),
                headers, table, cmd_proc)
        elif 'create' == operation:
            utils.print_message("creating cluster '%s'" %
                                (cluster_name))
            r = cse.create_cluster(cluster_name, worker_count)
            if 'task_id' in r:
                t = Task(session=cmd_proc.vca.vcloud_session,
                         verify=cmd_proc.verify,
                         log=cmd_proc.vca.log)
                task = t.get_task(r['task_id'])
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                utils.print_error("can't create the cluster", cmd_proc)
                sys.exit(1)
        elif 'delete' == operation:
            utils.print_message("deleting cluster '%s'" %
                                (cluster_id))
            r = cse.delete_cluster(cluster_id)
            if 'task_id' in r:
                t = Task(session=cmd_proc.vca.vcloud_session,
                         verify=cmd_proc.verify,
                         log=cmd_proc.vca.log)
                task = t.get_task(r['task_id'])
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                utils.print_error("can't delete the cluster", cmd_proc)
                sys.exit(1)
        else:
            utils.print_error('not implemented', cmd_proc)
            sys.exit(1)
    cmd_proc.save_current_config()
