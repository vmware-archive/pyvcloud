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


import sys
import click
import yaml
import json
import operator
from vca_cli import cli, utils, default_operation
from pyvcloud.score import Score
from dsl_parser.exceptions import \
    MissingRequiredInputError, \
    UnknownInputError, \
    FunctionEvaluationError, \
    DSLParsingException
from pyvcloud import Log
import print_utils
from tabulate import tabulate
import collections


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | validate | upload | delete | status]',
                type=click.Choice(['list', 'info', 'validate', 'upload',
                                   'delete', 'status']))
@click.option('-b', '--blueprint', default='',
              metavar='<blueprint-id>',
              help='Name of the blueprint to create')
@click.option('-f', '--file', 'blueprint_file',
              default=None, metavar='<blueprint-file>',
              help='Local file name of the blueprint to upload',
              type=click.Path(exists=True))
@click.option('-p', '--include-plan', is_flag=True, default=False,
              metavar="include_plan",
              help="Include blueprint plan in INFO operation")
def blueprint(cmd_proc, operation, blueprint, blueprint_file, include_plan):
    """Operations with Blueprints"""
    score = None
    if 'validate' != operation:
        result = cmd_proc.re_login()
        if not result:
            utils.print_error('Not logged in', cmd_proc)
            sys.exit(1)
        score = cmd_proc.vca.get_score_service(cmd_proc.host_score)
        if score is None:
            utils.print_error('Unable to access the blueprint service',
                              cmd_proc)
            sys.exit(1)
    else:
        score = Score(cmd_proc.host_score)
        Log.debug(cmd_proc.logger, 'using host score: %s' %
                  cmd_proc.host_score)
    if 'validate' == operation:
        try:
            score.blueprints.validate(blueprint_file)
            utils.print_message("The blueprint is valid.", cmd_proc)
        except MissingRequiredInputError as mrie:
            utils.print_error('Invalid blueprint: ' +
                              str(mrie)[str(mrie).rfind('}') + 1:].
                              strip())
        except UnknownInputError as uie:
            utils.print_error('Invalid blueprint: ' +
                              str(uie)[str(uie).rfind('}') + 1:].
                              strip())
        except FunctionEvaluationError as fee:
            utils.print_error('Invalid blueprint: ' +
                              str(fee)[str(fee).rfind('}') + 1:].
                              strip())
        except DSLParsingException as dpe:
            utils.print_error('Invalid blueprint: ' +
                              str(dpe)[str(dpe).rfind('}') + 1:].
                              strip())
        except Exception as ex:
            utils.print_error('Failed to validate %s:\n %s' %
                              (blueprint_file, str(ex)))
    elif 'status' == operation:
        status = score.get_status()
        print status
    elif 'list' == operation:
        blueprints = score.blueprints.list()
        if blueprints is None or len(blueprints) == 0:
            utils.print_message('No blueprints found. Reason %s.' %
                                str(score.response.content), cmd_proc)
            return
        headers = ['Id', 'Created']
        table = cmd_proc.blueprints_to_table(blueprints)
        if cmd_proc.json_output:
            json_object = {'blueprints':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Available blueprints, profile '%s':" %
                              (cmd_proc.profile),
                              headers, table, cmd_proc)
    elif 'upload' == operation:
        try:
            b = score.blueprints.upload(blueprint_file, blueprint)
            if b is not None:
                utils.print_message("Successfully uploaded blueprint '%s'." %
                                    b.get('id'), cmd_proc)
        except Exception:
            utils.print_error("Failed to upload blueprint. Reason: %s." %
                              str(score.response.content), cmd_proc)
    elif 'delete' == operation:
        b = score.blueprints.delete(blueprint)
        if b:
            utils.print_message("successfully deleted blueprint '%s'" %
                                blueprint, cmd_proc)
        else:
            utils.print_error("Failed to delete blueprint. Reason: %s." %
                              str(score.response.content), cmd_proc)
    elif 'info' == operation:
        b = score.blueprints.get(blueprint)
        if b:
            headers = ['Id', 'Created']
            table = cmd_proc.blueprints_to_table([b])
            if cmd_proc.json_output:
                json_object = {'blueprint':
                               utils.table_to_json(headers, table)}
                utils.print_json(json_object, cmd_proc=cmd_proc)
            else:
                utils.print_table("Details of blueprint '%s', profile '%s':" %
                                  (blueprint, cmd_proc.profile),
                                  headers, table, cmd_proc)
                if include_plan:
                    print(b['plan'])
        else:
            utils.print_error("Blueprint not found. Reason: %s." %
                              str(score.response.content))


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
            inputs_view.append(inputs_line % (
                dep['inputs'].keys()[i],
                dep['inputs'].values()[i]))
        dep['inputs'] = "\n".join(inputs_view)
        print_utils.print_list(
            [dep],
            ['blueprint_id', 'id', 'created_at', 'inputs'],
            obj_is_dict=True)


def print_deployment_info(deployment, executions, events, ctx=None):
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
    headers = ['Workflow', 'Created', 'Status', 'Id']
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
                    [event.get('event_type'), event.get('timestamp'),
                     event.get('message').get('text')])
        print_table("Events for workflow '%s'" %
                    deployment.get('workflow_id'), 'events',
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
                metavar='[list | info | create | delete | execute | cancel]',
                type=click.Choice(['list', 'info',
                                   'create', 'delete', 'execute', 'cancel']))
@click.option('-w', '--workflow', default=None,
              metavar='<workflow-id>', help='Workflow Id')
@click.option('-d', '--deployment', default='',
              metavar='<deployment-id>', help='Deployment Id')
@click.option('-b', '--blueprint', default=None,
              metavar='<blueprint-id>', help='Blueprint Id')
@click.option('-f', '--file', 'input_file', default=None,
              metavar='<input-file>',
              help='Local file with the input values '
                   'for the deployment (YAML)',
              type=click.File('r'))
@click.option('-s', '--show-events', 'show_events',
              is_flag=True, default=False, help='Show events')
@click.option('-e', '--execution', default=None,
              metavar='<execution-id>', help='Execution Id')
@click.option('--force', 'force_cancel',
              is_flag=True, default=False, help='Force cancel execution')
def deployment(cmd_proc, operation, deployment, blueprint,
               input_file, workflow, show_events, execution, force_cancel):
    """Operations with Deployments"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    score = cmd_proc.vca.get_score_service(cmd_proc.host_score)
    if score is None:
        utils.print_error('Unable to access the blueprint service',
                          cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        deployments = score.deployments.list()
        if deployments is None or len(deployments) == 0:
            utils.print_message('No deployments found. Reason %s.' %
                                str(score.response.content), cmd_proc)
            return
        print_deployments(deployments)
    elif 'create' == operation:
        inputs = None
        if input_file:
            inputs = yaml.load(input_file)
        d = score.deployments.create(
            blueprint, deployment,
            json.dumps(inputs, sort_keys=False,
                       indent=4, separators=(',', ': ')))
        if d:
            utils.print_message("Successfully created deployment '%s'." %
                                deployment, cmd_proc)
        else:
            utils.print_error("Failed to create deployment. Reason: %s" %
                              str(score.response.content), cmd_proc)
    elif 'delete' == operation:
        d = score.deployments.delete(deployment)
        if d:
            utils.print_message("successfully deleted deployment '%s'" %
                                deployment, cmd_proc)
        else:
            utils.print_error("Failed to delete deployment. Reason: %s." %
                              str(score.response.content), cmd_proc)
    elif 'info' == operation:
        d = score.deployments.get(deployment)
        if d is not None:
            e = score.executions.list(deployment)
            events = None
            if show_events and e is not None and len(e) > 0:
                events = score.events.get(e[-1].get('id'))
            print_deployment_info(d, e, events)
        else:
            utils.print_error("deployment not found")
    elif 'execute' == operation:
        if not deployment or not workflow:
            utils.print_error("Deployment ID or Workflow ID "
                              "was not specified.")
        e = score.executions.start(deployment, workflow)
        print_utils.print_dict(e) if e else utils.print_message(
            str(score.response.content), cmd_proc)
    elif 'cancel' == operation:
        if not execution:
            utils.print_error("execution id is not specified")
            return
        e = score.executions.cancel(execution, force_cancel)
        print_execution(e, None) if e else utils.print_message(
            str(score.response.content), cmd_proc)


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list]',
                type=click.Choice(['list']))
@click.option('-i', '--id', 'execution', metavar='<execution-id>',
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
def event(cmd_proc, operation, execution, from_event, batch_size, show_logs):
    """Operations with Blueprint Events"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    score = cmd_proc.vca.get_score_service(cmd_proc.host_score)
    if score is None:
        utils.print_error('Unable to access the blueprint service',
                          cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        events = score.events.get(execution, from_event=from_event,
                                  batch_size=batch_size,
                                  include_logs=show_logs)
        if not events or len(events) == 1:
            utils.print_error("Can't find events for execution: {0}. "
                              "Reason: {1}.".
                              format(execution, str(score.response.content)),
                              cmd_proc)
        else:
            print_table("Status:", 'status', events[0].keys(),
                        [e.values() for e in events[:-1]], None)
            utils.print_message("Total events: {}".format(events[-1]),
                                cmd_proc)
