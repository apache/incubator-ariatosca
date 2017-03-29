# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys
import difflib
import StringIO
import traceback
from functools import wraps

import click

from ..env import env, logger
from ..cli import helptexts
from ..inputs import inputs_to_dict
from ..constants import SAMPLE_SERVICE_TEMPLATE_FILENAME
from ...utils.exceptions import get_exception_as_string


CLICK_CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    token_normalize_func=lambda param: param.lower())


class MutuallyExclusiveOption(click.Option):
    """Makes options mutually exclusive. The option must pass a `cls` argument
    with this class name and a `mutually_exclusive` argument with a list of
    argument names it is mutually exclusive with.

    NOTE: All mutually exclusive options must use this. It's not enough to
    use it in just one of the options.
    """

    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        self.mutuality_error_message = \
            kwargs.pop('mutuality_error_message',
                       helptexts.DEFAULT_MUTUALITY_MESSAGE)
        self.mutuality_string = ', '.join(self.mutually_exclusive)
        if self.mutually_exclusive:
            help = kwargs.get('help', '')
            kwargs['help'] = (
                '{0}. This argument is mutually exclusive with '
                'arguments: [{1}] ({2})'.format(
                    help,
                    self.mutuality_string,
                    self.mutuality_error_message))
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                'Illegal usage: `{0}` is mutually exclusive with '
                'arguments: [{1}] ({2}).'.format(
                    self.name,
                    self.mutuality_string,
                    self.mutuality_error_message))
        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx, opts, args)


def _format_version_data(version_data,
                         prefix=None,
                         suffix=None,
                         infix=None):
    all_data = version_data.copy()
    all_data['prefix'] = prefix or ''
    all_data['suffix'] = suffix or ''
    all_data['infix'] = infix or ''
    output = StringIO.StringIO()
    output.write('{prefix}{version}'.format(**all_data))
    output.write('{suffix}'.format(**all_data))
    return output.getvalue()


def show_version(ctx, param, value):
    if not value:
        return

    cli_version_data = env.get_version_data()
    cli_version = _format_version_data(
        cli_version_data,
        prefix='ARIA CLI ',
        infix=' ' * 5,
        suffix='')

    logger.info(cli_version)
    ctx.exit()


def inputs_callback(ctx, param, value):
    """Allow to pass any inputs we provide to a command as
    processed inputs instead of having to call `inputs_to_dict`
    inside the command.

    `@aria.options.inputs` already calls this callback so that
    every time you use the option it returns the inputs as a
    dictionary.
    """
    if not value:
        return {}

    return inputs_to_dict(value)


def set_verbosity_level(ctx, param, value):
    if not value:
        return

    env.logging.verbosity_level = value


def set_cli_except_hook(global_verbosity_level):

    def recommend(possible_solutions):
        logger.info('Possible solutions:')
        for solution in possible_solutions:
            logger.info('  - {0}'.format(solution))

    def new_excepthook(tpe, value, tb):
        if global_verbosity_level:
            # log error including traceback
            logger.error(get_exception_as_string(tpe, value, tb))
        else:
            # write the full error to the log file
            with open(env.logging.log_file, 'a') as log_file:
                traceback.print_exception(
                    etype=tpe,
                    value=value,
                    tb=tb,
                    file=log_file)
            # print only the error message
            print value

        if hasattr(value, 'possible_solutions'):
            recommend(getattr(value, 'possible_solutions'))

    sys.excepthook = new_excepthook


def pass_logger(func):
    """Simply passes the logger to a command.
    """
    # Wraps here makes sure the original docstring propagates to click
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(logger=logger, *args, **kwargs)

    return wrapper


def pass_plugin_manager(func):
    """Simply passes the plugin manager to a command.
    """
    # Wraps here makes sure the original docstring propagates to click
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(plugin_manager=env.plugin_manager, *args, **kwargs)

    return wrapper


def pass_model_storage(func):
    """Simply passes the model storage to a command.
    """
    # Wraps here makes sure the original docstring propagates to click
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(model_storage=env.model_storage, *args, **kwargs)

    return wrapper


def pass_resource_storage(func):
    """Simply passes the resource storage to a command.
    """
    # Wraps here makes sure the original docstring propagates to click
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(resource_storage=env.resource_storage, *args, **kwargs)

    return wrapper


def pass_context(func):
    """Make click context ARIA specific

    This exists purely for aesthetic reasons, otherwise
    Some decorators are called `@click.something` instead of
    `@aria.something`
    """
    return click.pass_context(func)


class AliasedGroup(click.Group):
    def __init__(self, *args, **kwargs):
        self.max_suggestions = kwargs.pop("max_suggestions", 3)
        self.cutoff = kwargs.pop("cutoff", 0.5)
        super(AliasedGroup, self).__init__(*args, **kwargs)

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = \
            [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: {0}'.format(', '.join(sorted(matches))))

    def resolve_command(self, ctx, args):
        """Override clicks ``resolve_command`` method
        and appends *Did you mean ...* suggestions
        to the raised exception message.
        """
        try:
            return super(AliasedGroup, self).resolve_command(ctx, args)
        except click.exceptions.UsageError as error:
            error_msg = str(error)
            original_cmd_name = click.utils.make_str(args[0])
            matches = difflib.get_close_matches(
                original_cmd_name,
                self.list_commands(ctx),
                self.max_suggestions,
                self.cutoff)
            if matches:
                error_msg += '\n\nDid you mean one of these?\n    {0}'.format(
                    '\n    '.join(matches))
            raise click.exceptions.UsageError(error_msg, error.ctx)


def group(name):
    """Allow to create a group with a default click context
    and a cls for click's `didyoueamn` without having to repeat
    it for every group.
    """
    return click.group(
        name=name,
        context_settings=CLICK_CONTEXT_SETTINGS,
        cls=AliasedGroup)


def command(*args, **kwargs):
    """Make Click commands ARIA specific

    This exists purely for aesthetical reasons, otherwise
    Some decorators are called `@click.something` instead of
    `@aria.something`
    """
    return click.command(*args, **kwargs)


def argument(*args, **kwargs):
    """Make Click arguments ARIA specific

    This exists purely for aesthetic reasons, otherwise
    Some decorators are called `@click.something` instead of
    `@aria.something`
    """
    return click.argument(*args, **kwargs)


class Options(object):
    def __init__(self):
        """The options api is nicer when you use each option by calling
        `@aria.options.some_option` instead of `@aria.some_option`.

        Note that some options are attributes and some are static methods.
        The reason for that is that we want to be explicit regarding how
        a developer sees an option. It it can receive arguments, it's a
        method - if not, it's an attribute.
        """
        self.version = click.option(
            '--version',
            is_flag=True,
            callback=show_version,
            expose_value=False,
            is_eager=True,
            help=helptexts.VERSION)

        self.inputs = click.option(
            '-i',
            '--inputs',
            multiple=True,
            callback=inputs_callback,
            help=helptexts.INPUTS)

        self.output_path = click.option(
            '-o',
            '--output-path',
            help=helptexts.OUTPUT_PATH)

        self.optional_output_path = click.option(
            '-o',
            '--output-path',
            help=helptexts.OUTPUT_PATH)

        self.json_output = click.option(
            '--json-output',
            is_flag=True,
            help=helptexts.JSON_OUTPUT)

        self.init_hard_reset = click.option(
            '--hard',
            is_flag=True,
            help=helptexts.HARD_RESET)

        self.reset_context = click.option(
            '-r',
            '--reset-context',
            is_flag=True,
            help=helptexts.RESET_CONTEXT)

        self.enable_colors = click.option(
            '--enable-colors',
            is_flag=True,
            default=False,
            help=helptexts.ENABLE_COLORS)

        self.node_name = click.option(
            '-n',
            '--node-name',
            required=False,
            help=helptexts.NODE_NAME)

        self.descending = click.option(
            '--descending',
            required=False,
            is_flag=True,
            default=False,
            help=helptexts.DESCENDING)

    @staticmethod
    def verbose(expose_value=False):
        return click.option(
            '-v',
            '--verbose',
            count=True,
            callback=set_verbosity_level,
            expose_value=expose_value,
            is_eager=True,
            help=helptexts.VERBOSE)

    @staticmethod
    def force(help):
        return click.option(
            '-f',
            '--force',
            is_flag=True,
            help=help)

    @staticmethod
    def service_template_filename():
        return click.option(
            '-n',
            '--service-template-filename',
            default=SAMPLE_SERVICE_TEMPLATE_FILENAME,
            help=helptexts.SERVICE_TEMPLATE_FILENAME)

    @staticmethod
    def workflow_id(default):
        return click.option(
            '-w',
            '--workflow-id',
            default=default,
            help=helptexts.WORKFLOW_TO_EXECUTE.format(default))

    @staticmethod
    def task_thread_pool_size(default=1):
        return click.option(
            '--task-thread-pool-size',
            type=int,
            default=default,
            help=helptexts.TASK_THREAD_POOL_SIZE.format(default))

    @staticmethod
    def task_max_attempts(default=1):
        return click.option(
            '--task-max-attempts',
            type=int,
            default=default,
            help=helptexts.TASK_MAX_ATTEMPTS.format(default))

    @staticmethod
    def sort_by(default='created_at'):
        return click.option(
            '--sort-by',
            required=False,
            default=default,
            help=helptexts.SORT_BY)

    @staticmethod
    def task_retry_interval(default=1):
        return click.option(
            '--task-retry-interval',
            type=int,
            default=default,
            help=helptexts.TASK_RETRY_INTERVAL.format(default))

    @staticmethod
    def timeout(default=900):
        #TODO needed?
        return click.option(
            '--timeout',
            type=int,
            default=default,
            help=helptexts.OPERATION_TIMEOUT)

    @staticmethod
    def service_id(required=False):
        return click.option(
            '-s',
            '--service-id',
            required=required,
            help=helptexts.SERVICE_ID)

    @staticmethod
    def execution_id(required=False):
        return click.option(
            '-e',
            '--execution-id',
            required=required,
            help=helptexts.EXECUTION_ID)

    @staticmethod
    def service_template_id(required=False):
        return click.option(
            '-t',
            '--service-template-id',
            required=required,
            help=helptexts.SERVICE_TEMPLATE_ID)

    @staticmethod
    def service_template_path(required=False):
        return click.option(
            '-p',
            '--service-template-path',
            required=required,
            type=click.Path(exists=True))

    @staticmethod
    def service_name(required=False):
        return click.option(
            '-s',
            '--service-name',
            required=required,
            help=helptexts.SERVICE_ID)

    @staticmethod
    def service_template_name(required=False):
        return click.option(
            '-t',
            '--service-template-name',
            required=required,
            help=helptexts.SERVICE_ID)


options = Options()
