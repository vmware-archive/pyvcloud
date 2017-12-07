import click

from pyvcloud.vcd.org import Org

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with rights')
@click.pass_context
def right(ctx):
    """Work with rights

\b
    Examples
        vcd right list
            Get list of roles in the specified or current organization.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@right.command('list', short_help='list rights in the specified or current org')
@click.pass_context
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='<org_name>',
              help='name of the org')
def list_rights(ctx, org_name):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, org_href)
        result = org.list_rights()
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)