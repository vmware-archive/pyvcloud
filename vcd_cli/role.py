import click
from pyvcloud.vcd.org import Org

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with roles')
@click.pass_context
def role(ctx):
    """Work with roles in current organization.

\b
    Examples
        vcd role list
            Get list of roles in current organization.
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
