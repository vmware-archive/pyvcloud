import click
from pyvcloud.vcd.org import Org

from vcd_cli.utils import stderr, restore_session, stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with users in current organization')
@click.pass_context
def user(ctx):
    """Work with users in current organization.

\b
    Examples
        vcd user create my-user my-password role-name
           create user in the current organization with my-user password and role-name .
\b
        vcd user create 'my user' 'my password' 'role name'
           create user in the current organization with 'my user' 'my password' and 'role name' .

    """  # NOQA
    if ctx.invoked_subcommand not in [None, 'item']:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@user.command(short_help='create user in current organization')
@click.pass_context
@click.argument('user_name',
                metavar='<user_name>',
                required=True)
@click.argument('password',
                metavar='<password>',
                required=True)
@click.argument('role_name',
                metavar='<role-name>',
                required=True)
@click.option('-e',
              '--email',
              required=False,
              default='',
              metavar='[email]',
              help='User\'s email address.')
@click.option('-f',
              '--full-name',
              required=False,
              default='',
              metavar='[full_name]',
              help='Full name of the user.')
@click.option('-D',
              '--description',
              required=False,
              default='',
              metavar='[description]',
              help='description.')
@click.option('-t',
              '--telephone',
              required=False,
              default='',
              metavar='[telephone]',
              help='User\'s telephone number.')
@click.option('-i',
              '--im',
              required=False,
              default='',
              metavar='[im]',
              help='User\'s im address.')
@click.option('-E',
              '--enabled',
              is_flag=True,
              required=False,
              default=False,
              metavar='[enabled]',
              help='Enable user')
@click.option('--alert-enabled',
              is_flag=True,
              required=False,
              default=False,
              metavar='[alert_enabled]',
              help='Enable alerts')
@click.option('--alert-email',
              required=False,
              default='',
              metavar='[alert_email]',
              help='Alert email address')
@click.option('--alert-email-prefix',
              required=False,
              default='',
              metavar='[alert_email_prefix]',
              help='String to prepend to the alert message subject line')
@click.option('--external',
              is_flag=True,
              required=False,
              default=False,
              metavar='[is_external]',
              help='Indicates if user is imported from an external source')
@click.option('--default-cached',
              is_flag=True,
              required=False,
              default=False,
              metavar='[default_cached]',
              help='Indicates if user should be cached')
@click.option('-g',
              '--group-role',
              is_flag=True,
              required=False,
              default=False,
              metavar='[is_group_role]',
              help='Indicates if the user has a group role')
@click.option('-s',
              '--stored-vm-quota',
              required=False,
              default=0,
              metavar='[stored_vm_quota]',
              help='Quota of vApps that this user can store')
@click.option('-d',
              '--deployed-vm-quota',
              required=False,
              default=0,
              metavar='[deployed_vm_quota]',
              help='Quota of vApps that this user can deploy concurrently')
def create(ctx, user_name, password, role_name, full_name, description, email,
           telephone, im, enabled, alert_enabled, alert_email,
           alert_email_prefix, external, default_cached, group_role,
           stored_vm_quota, deployed_vm_quota):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org_in_use')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        role = org.get_role(role_name)
        role_href = role.get('href')
        u = org.create_user(user_name, password, role_href, full_name,
                            description, email, telephone, im,
                            alert_email, alert_email_prefix,
                            stored_vm_quota, deployed_vm_quota, group_role,
                            default_cached, external, alert_enabled,
                            enabled)
        stdout('User \'%s\' is successfully created.' % u.get('name'), ctx)
    except Exception as e:
        stderr(e, ctx)
