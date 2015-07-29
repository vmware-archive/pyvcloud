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
from vca_cli import cli, utils, default_operation
from pyvcloud.score import Score
from dsl_parser.exceptions import \
    MissingRequiredInputError, \
    UnknownInputError, \
    FunctionEvaluationError, \
    DSLParsingException
from pyvcloud import Log


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | validate | upload | delete]',
                type=click.Choice(['list', 'info', 'validate', 'upload',
                                   'delete']))
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
            utils.print_error('Unable to access the blueprints service',
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
              help='Local file with the input values'
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
        utils.print_error('Unable to access the blueprints service',
                          cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        pass
