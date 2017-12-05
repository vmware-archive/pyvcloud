import click
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.role import Role

from vcd_cli.utils import is_sysadmin
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with roles')
@click.pass_context
def role(ctx):
    """Work with roles and rights

\b
    Examples
        vcd role list
            Get list of roles in the current organization.
            
        vcd role list_rights
            Get list of rights in a given role.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@role.command('list', short_help='list roles')
@click.pass_context
def list_roles(ctx):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        result = org.list_roles()
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@role.command('list_rights', short_help='list rights of a role')
@click.pass_context
@click.argument('role-name',
                metavar='<role-name>',
                required=True)
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='<org-name>',
              help='name of the org')
def list_rights(ctx, role_name, org_name=None):
    try:
        client = ctx.obj['client']
        if (org_name is not None):
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, org_href, is_sysadmin(ctx))
        role_record = org.get_role(role_name)
        role = Role(client, href=role_record.get('href'))
        rights = role.list_rights()
        stdout(rights, ctx)
    except Exception as e:
        stderr(e, ctx)
