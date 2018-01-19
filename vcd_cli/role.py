import click

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.role import Role

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.utils import to_dict
from vcd_cli.vcd import abort_if_false
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with roles')
@click.pass_context
def role(ctx):
    """Work with roles.

\b
    Note
       All sub-commands execute in the context of organization specified
       via --org option; it defaults to current organization-in-use
       if --org option is not specified.

\b
    Examples
        vcd role list
            Get list of roles in the current organization.

\b
        vcd role list-rights myRole
            Get list of rights associated with a given role.

\b
        vcd role create myRole myDescription 'Disk: View Properties' \\
            'Provider vDC: Edit' --org myOrg
            Creates a role with zero or more rights.

\b
        vcd role delete myRole -o myOrg
            Deletes a role from the organization.

\b
        vcd role link myRole -o myOrg
            Links the role to it's original template.

\b
        vcd role unlink myRole -o myOrg
            Unlinks the role from its template.

\b
        vcd role add-right myRole myRight1 myRight2  -o myOrg
            Adds one or more rights to a given role.

\b
        vcd role remove-right myRole myRight1 myRight2  -o myOrg
            Removes one or more rights from a given role.

    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@role.command('list', short_help='list roles')
@click.pass_context
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org',
              )
def list_roles(ctx, org_name):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        roles = org.list_roles()
        for role in roles:
            del role['href']
        stdout(roles, ctx)
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
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
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
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        role = org.create_role(role_name, description, rights)
        stdout(to_dict(role, exclude=['Link', 'RightReferences']), ctx)
    except Exception as e:
        stderr(e, ctx)


@role.command('delete', short_help='Deletes role in the specified Organization')
@click.pass_context
@click.argument('role-name',
                metavar='<role-name>',
                required=True)
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org')
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to delete the role?')
def delete(ctx, role_name, org_name):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        org.delete_role(role_name)
        stdout('Role \'%s\' has been successfully deleted.' % role_name, ctx)
    except Exception as e:
        stderr(e, ctx)


@role.command('unlink', short_help='Unlink the role of a given org'
                                   ' from its template')
@click.pass_context
@click.argument('role-name',
                metavar='<role-name>',
                required=True)
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org')
def unlink(ctx, role_name, org_name):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        role_record = org.get_role(role_name)
        role = Role(client, href=role_record.get('href'))
        role.unlink()
        stdout('Role \'%s\' has been successfully unlinked'
               ' from it\'s template.' % role_name, ctx)
    except Exception as e:
        stderr(e, ctx)


@role.command('link', short_help='Link the role of a given org'
                                 ' to its template')
@click.pass_context
@click.argument('role-name',
                metavar='<role-name>',
                required=True)
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org')
def link(ctx, role_name, org_name):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        role_record = org.get_role(role_name)
        role = Role(client, href=role_record.get('href'))
        role.link()
        stdout('Role \'%s\' has been successfully linked'
               ' to it\'s template.' % role_name, ctx)
    except Exception as e:
        stderr(e, ctx)


@role.command('add-right', short_help='Adds one or more rights to the role')
@click.pass_context
@click.argument('role-name',
                metavar='<role-name>',
                required=True)
@click.argument('rights',
                nargs=-1,
                required=True)
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org')
def add_right(ctx, role_name, rights, org_name):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        role_record = org.get_role(role_name)
        role = Role(client, href=role_record.get('href'))
        role.add_rights(list(rights), org)
        stdout('Rights added successfully to the role \'%s\'' % role_name, ctx)
    except Exception as e:
        stderr(e, ctx)


@role.command('remove-right', short_help='Removes one or more rights'
                                         ' from the role')
@click.pass_context
@click.argument('role-name',
                metavar='<role-name>',
                required=True)
@click.argument('rights',
                nargs=-1,
                required=True)
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org')
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to remove rights from the role?')
def remove_right(ctx, role_name, rights, org_name):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        role_record = org.get_role(role_name)
        role = Role(client, href=role_record.get('href'))
        role.remove_rights(list(rights))
        stdout('Removed rights successfully from the role \'%s\'' % role_name, ctx)
    except Exception as e:
        stderr(e, ctx)
