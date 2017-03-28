import aria.cli.commands as commands
import click.testing


def invoke(command_string):
    command_list = command_string.split()
    command, sub, args = command_list[0], command_list[1], command_list[2:]
    runner = click.testing.CliRunner()
    outcome = runner.invoke(getattr(
        getattr(commands, command), sub), args)
    return outcome
