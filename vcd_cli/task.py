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
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.utils import task_to_dict
from vcd_cli.utils import as_metavar
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with tasks')
@click.pass_context
def task(ctx):
    """Work with tasks in vCloud Director.

\b
    Examples
        vcd task list running
            Get list of running tasks.
\b
        vcd task info 4a115aa5-9657-4d97-a8c2-3faf43fb45dd
            Get details of task by id.
\b
        vcd task wait 4a115aa5-9657-4d97-a8c2-3faf43fb45dd
            Wait until task is complete.
\b
        vcd task update aborted 4a115aa5-9657-4d97-a8c2-3faf43fb45dd
            Abort task by id, requires login as 'system administrator'.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@task.command(short_help='show task details')
@click.pass_context
@click.argument('task_id',
                metavar='<id>',
                required=True)
def info(ctx, task_id):
    try:
        client = ctx.obj['client']
        result = client.get_resource('%s/task/%s' % (client._uri, task_id))
        stdout(task_to_dict(result), ctx, show_id=True)
    except Exception as e:
        stderr(e, ctx)


@task.command(short_help='list tasks')
@click.pass_context
@click.argument('status',
                type=click.Choice(TaskStatus._enums.keys()),
                metavar=as_metavar(TaskStatus._enums.keys()),
                required=False)
def list(ctx, status):
    stdout('use the search command:')
    stdout('   vcd search task      --filter ''status==running''')
    stdout('   vcd search admintask --filter ''status==running''')


@task.command(short_help='wait until task is complete')
@click.pass_context
@click.argument('task_id',
                metavar='<id>',
                required=True)
def wait(ctx, task_id):
    try:
        client = ctx.obj['client']
        task = client.get_resource('%s/task/%s' % (client._uri, task_id))
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@task.command(short_help='update task status')
@click.pass_context
@click.argument('status',
                type=click.Choice(TaskStatus._enums.keys()),
                metavar=as_metavar(TaskStatus._enums.keys()),
                required=True)
@click.argument('task_id',
                metavar='<id>',
                required=True)
def update(ctx, status, task_id):
    try:
        client = ctx.obj['client']
        task = client.get_resource('%s/task/%s' % (client._uri, task_id))
        task.set('status', status)
        result = client.put_linked_resource(task,
                                            RelationType.EDIT,
                                            EntityType.TASK.value,
                                            task)
        # stdout(result, ctx)
        print(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        stderr(e, ctx)
