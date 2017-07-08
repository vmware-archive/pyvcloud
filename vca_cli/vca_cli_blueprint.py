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
import collections
import json
import operator
import print_utils
from pyvcloud import exceptions
from pyvcloud import Log
from pyvcloud.score import Score
import sys
from tabulate import tabulate
from vca_cli import cli
from vca_cli import default_operation
from vca_cli import utils
import yaml


def _authorize(cmd_proc):
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
    scoreclient = cmd_proc.vca.get_score_service(cmd_proc.host_score)
    if scoreclient is None:
        utils.print_error('Unable to access TOSCA service.',
                          cmd_proc)
    return scoreclient


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | validate | upload | delete | status]',
                type=click.Choice(['list', 'info', 'validate', 'upload',
                                   'delete', 'status']))
@click.option('-b', '--blueprint', 'blueprint_id', default='',
              metavar='<blueprint-id>',
              help='Name of the blueprint to create')
@click.option('-f', '--file', 'blueprint_file',
              default=None, metavar='<blueprint-file>',
              help='Local file name of the blueprint to upload',
              type=click.Path(exists=True))
@click.option('-p', '--include-plan', is_flag=True, default=False,
              metavar="include_plan",
              help="Include blueprint plan in INFO operation")
def blueprint(cmd_proc, operation, blueprint_id, blueprint_file, include_plan):
    """Operations with Blueprints"""

    if 'validate' != operation:
        scoreclient = _authorize(cmd_proc)
    else:
        scoreclient = Score(cmd_proc.host_score)
        Log.debug(cmd_proc.logger, 'using host score: %s' %
                  cmd_proc.host_score)

    _run_operation(cmd_proc, operation,
                   blueprint_id, blueprint_file,
                   include_plan, scoreclient)


def _run_operation(cmd_proc, operation, blueprint_id,
                   blueprint_file, include_plan, scoreclient):

    def operation_unknown(cmd_proc, operation, blueprint_id,
                          blueprint_file, include_plan, scoreclient):
        utils.print_error("Operation '{0}' not supported.".format(
            operation), cmd_proc)

    operation_mapping = {
        'validate': _validate,
        'list': _list_blueprints,
        'upload': _upload,
        'delete': _delete_blueprint,
        'info': _info_blueprint,
        'status': _status,
    }
    method = operation_mapping.get(operation, operation_unknown)

    method(cmd_proc, operation, blueprint_id,
           blueprint_file, include_plan, scoreclient)


def _status(cmd_proc, operation,
            blueprint_id, blueprint_file,
            include_plan, scoreclient):
    try:
        status = scoreclient.get_status()
        print_utils.print_dict(json.loads(status))
    except exceptions.ClientException as e:
        utils.print_error("Unable to get blueprinting service status. "
                          "Reason: {0}, {1}"
                          .format(str(e), scoreclient.response.content),
                          cmd_proc)


def _info_blueprint(cmd_proc, operation,
                    blueprint_id, blueprint_file,
                    include_plan, scoreclient):
    try:
        b = scoreclient.blueprints.get(blueprint_id)
        if blueprint_id is None or len(blueprint_id) == 0:
            utils.print_error('specify blueprint id')
            sys.exit(1)
        headers = ['Id', 'Created']
        table = cmd_proc.blueprints_to_table([b])
        if cmd_proc.json_output:
            json_object = {'blueprint':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Details of blueprint '%s', profile '%s':" %
                              (blueprint_id, cmd_proc.profile),
                              headers, table, cmd_proc)
        if include_plan:
            utils.print_json(b['plan'], "Blueprint plan", cmd_proc)
    except exceptions.ClientException as e:
                utils.print_error("Blueprint not found. Reason: {0}, {1}".
                                  format(str(e),
                                         scoreclient.response.content),
                                  cmd_proc)


def _delete_blueprint(cmd_proc, operation,
                      blueprint_id, blueprint_file,
                      include_plan, scoreclient):
    try:
        scoreclient.blueprints.delete(blueprint_id)
        utils.print_message("successfully deleted blueprint '%s'" %
                            blueprint_id, cmd_proc)
    except exceptions.ClientException as e:
        utils.print_error("Failed to delete blueprint. Reason: {0}, {1}"
                          .format(str(e), scoreclient.response.content),
                          cmd_proc)


def _upload(cmd_proc, operation,
            blueprint_id, blueprint_file,
            include_plan, scoreclient):
    try:
        b = scoreclient.blueprints.upload(blueprint_file, blueprint_id)
        utils.print_message("Successfully uploaded blueprint '%s'." %
                            b.get('id'), cmd_proc)
    except exceptions.ClientException as e:
        utils.print_error("Failed to upload blueprint. Reason: {0}, {1}"
                          .format(str(e), scoreclient.response.content),
                          cmd_proc)


def _list_blueprints(cmd_proc, operation, blueprint_id,
                     blueprint_file, include_plan, scoreclient):
    try:
        blueprints = scoreclient.blueprints.list()
        headers = ['Id', 'Created']
        table = cmd_proc.blueprints_to_table(blueprints)
        if cmd_proc.json_output:
            json_object = {'blueprints':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Available blueprints, profile '%s':" %
                              cmd_proc.profile,
                              headers, table, cmd_proc)
    except exceptions.ClientException as e:
        utils.print_message('Unable to list blueprints. Reason {0}, {1}'
                            .format(str(e), scoreclient.response.content),
                            cmd_proc)


def _validate(cmd_proc, operation,
              blueprint_id, blueprint_file,
              include_plan, scoreclient):
    try:
        scoreclient.blueprints.validate(blueprint_file)
        utils.print_message("The blueprint is valid.", cmd_proc)
    except Exception as ex:
        utils.print_error('Failed to validate %s:\n %s' %
                          (blueprint_file, str(ex)))


def print_table(msg, obj, headers, table, ctx):
    if (ctx is not None and ctx.obj is not
            None and ctx.obj['json_output']):
        data = [dict(zip(headers, row)) for row in table]
        print(json.dumps(
            {"Errorcode": "0", "Details": msg, obj: data},
            sort_keys=True, indent=4, separators=(',', ': ')))
    else:
        click.echo(click.style(msg, fg='blue'))
        print(tabulate(table, headers=headers,
                       tablefmt="orgtbl"))


def print_deployments(deployments):
    for dep in deployments:
        inputs_view = []
        inputs_line = "%s : %s"
        for i in range(len(dep['inputs'].keys())):
            value = dep['inputs'].values()[i]
            if 'password' in dep['inputs'].keys()[i]:
                value = '************'
            if len(str(value)) > 50:
                value = value[:50] + '...'
            inputs_view.append(inputs_line % (
                dep['inputs'].keys()[i],
                value))
        dep['inputs'] = "\n".join(inputs_view)
        print_utils.print_list(
            [dep],
            ['blueprint_id', 'id', 'created_at', 'inputs'],
            obj_is_dict=True)


def print_deployment_info(deployment, executions, events, execution_id,
                          ctx=None):
    headers = ['Blueprint Id', 'Deployment Id', 'Created', 'Workflows']
    table = []
    workflows = []
    for workflow in deployment.get('workflows'):
        workflows.append(workflow.get('name').encode('utf-8'))
    table.append(
        [deployment.get('blueprint_id'), deployment.get('id'),
         deployment.get('created_at')[:-7], utils.beautified(workflows)])
    print_table("Deployment information:\n-----------------------",
                'deployment',
                headers, table, ctx)
    print("\n")
    headers = ['Workflow', 'Created', 'Status', 'Execution Id']
    table = []
    if executions is None or len(executions) == 0:
        utils.print_message('no executions found', ctx)
        return
    for e in executions:
        table.append([e.get('workflow_id'),
                      e.get('created_at')[:-7],
                      e.get('status'), e.get('id')])
    sorted_table = sorted(table, key=operator.itemgetter(1), reverse=False)
    print_table("Workflow executions for deployment: '%s'"
                "\n----------------------------------"
                % deployment.get('id'), 'executions', headers, sorted_table,
                ctx)
    if events:
        headers = ['Type', 'Started', 'Message']
        table = []
        for event in events:
            if isinstance(
                    event, collections.Iterable) and 'event_type' in event:
                table.append(
                    [event.get('event_type'), event.get('timestamp')[:-9],
                     event.get('message').get('text')])
        print('\n')
        print_table("Events for execution id '%s'" %
                    execution_id, 'events',
                    headers, table, ctx)


def print_execution(execution, ctx=None):
    if execution:
        headers = ['Workflow', 'Created', 'Status', 'Message']
        table = []
        table.append([
            execution.get('workflow_id'),
            execution.get('created_at')[:-7],
            execution.get('status'),
            execution.get('error')])
        sorted_table = sorted(table,
                              key=operator.itemgetter(1),
                              reverse=False)
        print_table(
            "Workflow execution '%s' for deployment '%s'"
            % (execution.get('id'), execution.get('deployment_id')),
            'execution', headers, sorted_table, ctx)
    else:
        utils.print_message("No execution", ctx)


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | create | delete | execute | cancel '
                        '| output]',
                type=click.Choice(['list', 'info', 'create', 'delete',
                                   'execute', 'cancel', 'output'
                                   ]))
@click.option('-w', '--workflow', default=None,
              metavar='<workflow-id>', help='Workflow Id')
@click.option('-d', '--deployment', 'deployment_id', default='',
              metavar='<deployment-id>', help='Deployment Id')
@click.option('-b', '--blueprint', 'blueprint_id', default=None,
              metavar='<blueprint-id>', help='Blueprint Id')
@click.option('-f', '--file', 'input_file', default=None,
              metavar='<input-file>',
              help='Local file with the input values '
                   'for the deployment (YAML)',
              type=click.File('r'))
@click.option('-s', '--show-events', 'show_events',
              is_flag=True, default=False, help='Show events')
@click.option('-e', '--execution', 'execution_id', default=None,
              metavar='<execution-id>', help='Execution Id')
@click.option('--force-cancel', 'force_cancel',
              is_flag=True, default=False, help='Force cancel execution')
@click.option('--force-delete', 'force_delete',
              is_flag=True, default=False, help='Force delete deployment')
def deployment(cmd_proc, operation, deployment_id, blueprint_id,
               input_file, workflow, show_events, execution_id,
               force_cancel, force_delete):
    """Operations with Deployments"""
    scoreclient = _authorize(cmd_proc)

    _run_deployment_operation(
        cmd_proc, operation, deployment_id, blueprint_id,
        input_file, workflow, show_events, execution_id,
        force_cancel, force_delete, scoreclient)


def _run_deployment_operation(
        cmd_proc, operation, deployment_id, blueprint_id,
        input_file, workflow, show_events, execution_id,
        force_cancel, force_delete, scoreclient):

    def operation_unknown(
            cmd_proc, operation, deployment_id, blueprint_id,
            input_file, workflow, show_events, execution_id,
            force_cancel, force_delete, scoreclient):
        utils.print_error("Operation '{0}' not supported.".format(
            operation), cmd_proc)

    operation_mapping = {
        'list': _list_deployments,
        'create': _create_deployment,
        'info': _info_deployment,
        'delete': _delete_deployment,
        'execute': _execute_workflow,
        'cancel': _cancel,
        'output': _outputs,
    }

    method = operation_mapping.get(operation, operation_unknown)
    method(cmd_proc, operation, deployment_id, blueprint_id,
           input_file, workflow, show_events, execution_id,
           force_cancel, force_delete, scoreclient)


def _outputs(cmd_proc, operation, deployment_id, blueprint_id,
             input_file, workflow, show_events, execution_id,
             force_cancel, force_delete, scoreclient):
    try:

        deployment_outputs = scoreclient.deployments.outputs(deployment_id)
        utils.print_json(deployment_outputs)

    except exceptions.ClientException as e:
        utils.print_error("Failed to get deployment output. Reason: {0}, {1}"
                          .format(str(e), scoreclient.response.content),
                          cmd_proc)


def _cancel(cmd_proc, operation, deployment_id, blueprint_id,
            input_file, workflow, show_events, execution_id,
            force_cancel, force_delete, scoreclient):

    if not execution_id:
        utils.print_error("Execution id is not specified.")
        return
    try:
        e = scoreclient.executions.cancel(execution_id, force_cancel)
        print_execution(e, None) if e else utils.print_message(
            str(scoreclient.response.content), cmd_proc)
    except exceptions.ClientException as e:
        utils.print_error("Failed to cancel workflow. Reasons: {0}, {1}."
                          .format(str(e), scoreclient.response.content),
                          cmd_proc)


def _create_deployment(cmd_proc, operation, deployment_id, blueprint_id,
                       input_file, workflow, show_events, execution_id,
                       force_cancel, force_delete,
                       scoreclient):
    try:
        inputs = None
        if input_file:
            inputs = yaml.load(input_file)
        scoreclient.deployments.create(blueprint_id, deployment_id, inputs)
        utils.print_message("Successfully created deployment '{0}'.".format(
            deployment_id), cmd_proc)
    except exceptions.ClientException as e:
            utils.print_error("Failed to create deployment. Reason: {0}, {1}"
                              .format(str(e), scoreclient.response.content),
                              cmd_proc)


def _list_deployments(cmd_proc, operation, deployment_id, blueprint_id,
                      input_file, workflow, show_events, execution_id,
                      force_cancel, force_delete, scoreclient):

    try:
        deployments = scoreclient.deployments.list()
        print_deployments(deployments)
    except exceptions.ClientException as e:
        utils.print_message('No deployments found. Reason {0}, {1}'
                            .format(str(e),
                                    scoreclient.response.content),
                            cmd_proc)


def _delete_deployment(cmd_proc, operation, deployment_id, blueprint_id,
                       input_file, workflow, show_events, execution_id,
                       force_cancel, force_delete, scoreclient):
    try:
        scoreclient.deployments.delete(deployment_id,
                                       force_delete=force_delete)
        utils.print_message("successfully deleted deployment '{0}'"
                            .format(deployment_id), cmd_proc)
    except exceptions.ClientException as e:
        utils.print_error("Failed to delete deployment. Reason: {0}, {1}"
                          .format(str(e), scoreclient.response.content),
                          cmd_proc)


def _info_deployment(cmd_proc, operation, deployment_id, blueprint_id,
                     input_file, workflow, show_events, execution_id,
                     force_cancel, force_delete, scoreclient):
    try:
        d = scoreclient.deployments.get(deployment_id)
        e = scoreclient.executions.list(deployment_id)
        events = None
        e_id = None
        if show_events and e is not None and len(e) > 0:
            table = []
            for execution in e:
                table.append([execution.get('created_at'),
                              execution.get('id')])
            sorted_table = sorted(table,
                                  key=operator.itemgetter(0),
                                  reverse=True)
            e_id = sorted_table[0][1] if execution_id is None else execution_id
            events = scoreclient.events.get(e_id)
        print_deployment_info(d, e, events, e_id)
    except exceptions.ClientException as e:
        utils.print_error("Failed to get deployment info. Reason: {0}, {1}"
                          .format(str(e), scoreclient.response.content),
                          cmd_proc)


def _execute_workflow(cmd_proc, operation, deployment_id, blueprint_id,
                      input_file, workflow, show_events, execution_id,
                      force_cancel, force_delete, scoreclient):
    try:
        if not deployment_id or not workflow:
            utils.print_error("Deployment ID or Workflow ID "
                              "was not specified.")
            return
        e = scoreclient.executions.start(
            deployment_id, workflow)
        print_utils.print_dict(e) if e else utils.print_message(
            str(scoreclient.response.content), cmd_proc)
    except exceptions.ClientException as e:
            utils.print_error("Failed to execute workflow. Reasons: {0}, {1}"
                              .format(str(e), scoreclient.response.content),
                              cmd_proc)


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list]',
                type=click.Choice(['list']))
@click.option('-i', '--id', 'execution_id', metavar='<execution-id>',
              required=True, help='Execution Id')
@click.option('-f', '--from', 'from_event',
              default=0, metavar='<from_event>',
              help='From event')
@click.option('-s', '--size', 'batch_size',
              default=100, metavar='<batch_size>',
              help='Size batch of events')
@click.option('-l', '--show-logs', 'show_logs',
              is_flag=True, default=False,
              help='Show logs for event')
def event(cmd_proc, operation, execution_id, from_event, batch_size,
          show_logs):
    """Operations with Blueprint Events"""
    scoreclient = _authorize(cmd_proc)

    if 'list' == operation:
        try:
            events = scoreclient.events.get(execution_id,
                                            from_event=from_event,
                                            batch_size=batch_size,
                                            include_logs=show_logs)
            print_events(events)
            utils.print_message("Total events: {}".format(events[-1]),
                                cmd_proc)
        except exceptions.ClientException as e:
                utils.print_error("Can't find events for execution: {0}. "
                                  "Reason: {1}.".
                                  format(execution_id, str(e)),
                                  cmd_proc)


def print_events(events):
    for _event in events[:-1]:
        context = _event['context']
        del _event['context']
        utils.print_json(_event)
        utils.print_json(context)
        print("\n")
