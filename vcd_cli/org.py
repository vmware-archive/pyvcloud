# VMware vCloud Director CLI
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
from pyvcloud.vcd.client import get_links
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.system import System
from pyvcloud.vcd.utils import org_to_dict

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import abort_if_false
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with organizations')
@click.pass_context
def org(ctx):
    """Work with organizations in vCloud Director.

\b
    Examples
        vcd org list
            Get list of organizations.
\b
        vcd org info my-org
            Get details of the organization 'my-org'.
\b
        vcd org use my-org
            Set organization 'my-org' as default.
\b
        vcd org create my-org-name my-org-fullname
            Create organization with 'my-org-name' and 'my-org-fullname'
\b
        vcd org delete my-org-name
            Delete organization 'my-org-name'
\b
        vcd org update my-org-name --enable
            Update organization 'my-org-name', e.g. enable the organization
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@org.command(short_help='show org details')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def info(ctx, name):
    try:
        client = ctx.obj['client']
        logged_in_org_name = ctx.obj['profiles'].get('org')
        in_use_org_name = ctx.obj['profiles'].get('org_in_use')
        orgs = client.get_org_list()
        for org in [o for o in orgs.Org if hasattr(orgs, 'Org')]:
            if name == org.get('name'):
                resource = client.get_resource(org.get('href'))
                result = org_to_dict(resource)
                result['logged_in'] = logged_in_org_name == org.get('name')
                result['in_use'] = in_use_org_name == org.get('name')
                stdout(result, ctx)
                return
        raise Exception('not found')
    except Exception as e:
        stderr(e, ctx)


@org.command('list', short_help='list organizations')
@click.pass_context
def list_orgs(ctx):
    try:
        client = ctx.obj['client']
        logged_in_org_name = ctx.obj['profiles'].get('org')
        in_use_org_name = ctx.obj['profiles'].get('org_in_use')
        orgs = client.get_org_list()
        result = []
        for org in [o for o in orgs.Org if hasattr(orgs, 'Org')]:
            result.append({'name': org.get('name'),
                           'logged_in': logged_in_org_name == org.get('name'),
                           'in_use': in_use_org_name == org.get('name')})
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@org.command(short_help='set active organization')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def use(ctx, name):
    try:
        client = ctx.obj['client']
        orgs = client.get_org_list()
        for org in [o for o in orgs.Org if hasattr(orgs, 'Org')]:
            if name == org.get('name'):
                resource = client.get_resource(org.get('href'))
                in_use_vdc = ''
                vdc_href = ''
                in_use_vapp = ''
                vapp_href = ''
                for v in get_links(resource, media_type=EntityType.VDC.value):
                    in_use_vdc = v.name
                    vdc_href = v.href
                    break
                ctx.obj['profiles'].set('org_in_use', str(name))
                ctx.obj['profiles'].set('org_href', str(org.get('href')))
                ctx.obj['profiles'].set('vdc_in_use', str(in_use_vdc))
                ctx.obj['profiles'].set('vdc_href', str(vdc_href))
                ctx.obj['profiles'].set('vapp_in_use', str(in_use_vapp))
                ctx.obj['profiles'].set('vapp_href', vapp_href)
                message = 'now using org: \'%s\', vdc: \'%s\', vApp: \'%s\'.' \
                    % (name, in_use_vdc, in_use_vapp)
                stdout({
                    'org': name,
                    'vdc': in_use_vdc,
                    'vapp': in_use_vapp
                }, ctx, message)
                return
        raise Exception('not found')
    except Exception as e:
        stderr(e, ctx)


@org.command(short_help='create an organization')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.argument('full_name',
                metavar='<full_name>',
                required=True)
@click.option('-e',
              '--enabled',
              is_flag=True,
              required=False,
              default=False,
              metavar='[enabled]',
              help='Enable org')
def create(ctx, name, full_name, enabled):
    try:
        client = ctx.obj['client']
        sys_admin_resource = client.get_admin()
        system = System(client, admin_resource=sys_admin_resource)
        result = system.create_org(name, full_name, enabled)
        stdout('Org \'%s\' is successfully created.' % result.get('name'), ctx)
    except Exception as e:
        stderr(e, ctx)


@org.command(short_help='delete an organization')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-r',
              '--recursive',
              is_flag=True,
              help='removes the Org and any objects it contains that are in a '
                   'state that normally allows removal')
@click.option('-f',
              '--force',
              is_flag=True,
              help='pass this option along with --recursive to remove an Org'
                   ' and any objects it contains, regardless of their state')
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to delete the Org?')
def delete(ctx, name, recursive, force):
    try:
        client = ctx.obj['client']
        system = System(client)
        if force and recursive:
            click.confirm('Do you want to force delete \'%s\' and all '
                          'its objects recursively?' % name, abort=True)
        elif force:
            click.confirm('Do you want to force delete \'%s\'' % name,
                          abort=True)
        task = system.delete_org(name, force, recursive)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@org.command(short_help='update an organization')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('--enable/--disable',
              'is_enabled',
              default=None,
              help='enable/disable the org')
def update(ctx, name, is_enabled):
    try:
        client = ctx.obj['client']
        org = Org(client, resource=client.get_org_by_name(name))
        result = org.update_org(is_enabled=is_enabled)
        stdout('Org \'%s\' is successfully updated.' % result.get('name'), ctx)
    except Exception as e:
        stderr(e, ctx)
