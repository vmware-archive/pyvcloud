#!/usr/bin/env python3

import click
from subprocess import check_output
from vcd_cli.vcd import vcd

command_list = []


def generate_index_page(commands):
    last_level = 0
    with open('docs/commands.md', 'w') as out:
        out.write('<div class="clt">\n')
        for cmd_str in commands:
            page_name = cmd_str.replace(' ', '_')
            tokens = cmd_str.split()
            if len(tokens) > last_level:
                out.write('<ul><li>\n')
            elif len(tokens) < last_level:
                out.write('</li>\n')
                for n in range(last_level-len(tokens)):
                    out.write('</ul></li>\n')
                out.write('<li>\n')
            else:
                out.write('</li><li>\n')
            out.write('<a href="%s">%s</a>' % (page_name, tokens[-1]))
            last_level = len(tokens)
        for n in range(last_level):
            out.write('</li></ul>\n')
        out.write('</div>\n')


def generate_page(cmd_str):
    page_name = cmd_str.replace(' ', '_')
    file_name = 'docs/%s.md' % page_name
    with open(file_name, 'w') as out:
        print('processing %s' % file_name)
        tokens = (cmd_str + ' -h').split()
        output = check_output(tokens)
        out.write('```\n')
        out.write(output.decode())
        out.write('\n```\n')
        output = check_output(['git', 'add', file_name])


def process_command(cmd, ancestors=[]):
    cmd_str = ''
    for a in ancestors:
        cmd_str += a.name + ' '
    cmd_str += cmd.name
    command_list.append(cmd_str)
    if type(cmd) == click.core.Group:
        for k in sorted(cmd.commands.keys()):
            a = ancestors + [cmd]
            process_command(cmd.commands[k], ancestors=a)

try:
    output = check_output(['git', 'rm', '-rf', 'docs/vcd*.md'])
except:
    pass
try:
    output = check_output(['git', 'rm', '-rf', 'docs/commands.md'])
except:
    pass
process_command(vcd)
generate_index_page(command_list)
check_output(['git', 'add', 'docs/commands.md'])
for cmd_str in command_list:
    generate_page(cmd_str)
