import click

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.role import Role

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.utils import to_dict
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with roles')
@click.pass_context
def role(ctx):
    """Work with roles and rights

\b
    Examples
        vcd role list
            Get list of roles in the current organization.
\b
        vcd role list_rights myRole
            Get list of rights associated with a given role.
\b
        vcd role create myRole myDescription 'Disk: View Properties' \\
            'Provider vDC: Edit' --org myOrg
            Create a role with zero or more rights in the specified
            Organization (defaults to current Organization in use)
    """

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
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        result = org.list_roles()
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@role.command('list-rights', short_help='list rights of a role')
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
def list_rights(ctx, role_name, org_name):
    try:
        client = ctx.obj['client']
        if org_name is None:
            org_name = ctx.obj['profiles'].get('org_in_use')
        org = Org(client, resource=client.get_org_by_name(org_name))
        role_record = org.get_role(role_name)
        role = Role(client, href=role_record.get('href'))
        rights = role.list_rights()
        stdout(rights, ctx)
    except Exception as e:
        stderr(e, ctx)


@role.command('create', short_help='Creates role in the specified Organization'
              ' (defaults to the current Organization in use)')
@click.pass_context
@click.argument('role-name',
                metavar='<role-name>',
                required=True)
@click.argument('description',
                metavar='<description>',
                required=True)
@click.argument('rights',
                nargs=-1,
                metavar='<rights>')
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org',
              )
def create(ctx, role_name, description, rights, org_name):
    try:
        client = ctx.obj['client']
        if org_name is None:
            org_name = ctx.obj['profiles'].get('org_in_use')
        org = Org(client, resource=client.get_org_by_name(org_name))
        role = org.create_role(role_name, description, rights)
        stdout(to_dict(role, exclude=['Link', 'RightReferences']), ctx)
    except Exception as e:
        stderr(e, ctx)
