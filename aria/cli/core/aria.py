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

import os
import sys
import difflib
import traceback
import inspect
from functools import wraps

import click

from ..env import (
    env,
    logger
)
from .. import defaults
from .. import helptexts
from ..inputs import inputs_to_dict
from ... import __version__
from ... import aria_package_name
from ...utils.exceptions import get_exception_as_string


CLICK_CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    token_normalize_func=lambda param: param.lower())


class MutuallyExclusiveOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', tuple()))
        self.mutuality_description = kwargs.pop('mutuality_description',
                                                ', '.join(self.mutually_exclusive))
        self.mutuality_error = kwargs.pop('mutuality_error',
                                          helptexts.DEFAULT_MUTUALITY_ERROR_MESSAGE)
        if self.mutually_exclusive:
            help = kwargs.get('help', '')
            kwargs['help'] = '{0}. {1}'.format(help, self._message)
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if (self.name in opts) and self.mutually_exclusive.intersection(opts):
            raise click.UsageError('Illegal usage: {0}'.format(self._message))
        return super(MutuallyExclusiveOption, self).handle_parse_result(ctx, opts, args)

    @property
    def _message(self):
        return '{0} be used together with {1} ({2}).'.format(
            '{0} cannot'.format(', '.join(self.opts)) if hasattr(self, 'opts') else 'Cannot',
            self.mutuality_description,
            self.mutuality_error)


def mutually_exclusive_option(*param_decls, **attrs):
    """
    Decorator for mutually exclusive options.

    This decorator works similarly to `click.option`, but supports an extra ``mutually_exclusive``
    argument, which is a list of argument names with which the option is mutually exclusive.

    You can optionally also supply ``mutuality_description`` and ``mutuality_error`` to override the
    default messages.

    NOTE: All mutually exclusive options must use this. It's not enough to use it in just one of the
    options.
    """

    # NOTE: This code is copied and slightly modified from click.decorators.option and
    # click.decorators._param_memo. Unfortunately, using click's ``cls`` parameter support does not
    # work as is with extra decorator arguments.

    def decorator(func):
        if 'help' in attrs:
            attrs['help'] = inspect.cleandoc(attrs['help'])
        param = MutuallyExclusiveOption(param_decls, **attrs)
        if not hasattr(func, '__click_params__'):
            func.__click_params__ = []
        func.__click_params__.append(param)
        return func
    return decorator


def show_version(ctx, param, value):
    if not value:
        return

    logger.info('{0} {1}'.format(aria_package_name, __version__))
    ctx.exit()


def inputs_callback(ctx, param, value):
    """
    Allow to pass any inputs we provide to a command as processed inputs instead of having to call
    ``inputs_to_dict`` inside the command.

    ``@aria.options.inputs`` already calls this callback so that every time you use the option it
    returns the inputs as a dictionary.
    """
    if not value:
        return {}

    return inputs_to_dict(value)


def set_verbosity_level(ctx, param, value):
    if not value:
        return

    env.logging.verbosity_level = value


def set_cli_except_hook():
    def recommend(possible_solutions):
        logger.info('Possible solutions:')
        for solution in possible_solutions:
            logger.info('  - {0}'.format(solution))

    def new_excepthook(tpe, value, trace):
        if env.logging.is_high_verbose_level():
            # log error including traceback
            logger.error(get_exception_as_string(tpe, value, trace))
        else:
            # write the full error to the log file
            with open(env.logging.log_file, 'a') as log_file:
                traceback.print_exception(
                    etype=tpe,
                    value=value,
                    tb=trace,
                    file=log_file)
            # print only the error message
            print value

        if hasattr(value, 'possible_solutions'):
            recommend(getattr(value, 'possible_solutions'))

    sys.excepthook = new_excepthook


def pass_logger(func):
    """
    Simply passes the logger to a command.
    """
    # Wraps here makes sure the original docstring propagates to click
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(logger=logger, *args, **kwargs)

    return wrapper


def pass_plugin_manager(func):
    """
    Simply passes the plugin manager to a command.
    """
    # Wraps here makes sure the original docstring propagates to click
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(plugin_manager=env.plugin_manager, *args, **kwargs)

    return wrapper


def pass_model_storage(func):
    """
    Simply passes the model storage to a command.
    """
    # Wraps here makes sure the original docstring propagates to click
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(model_storage=env.model_storage, *args, **kwargs)

    return wrapper


def pass_resource_storage(func):
    """
    Simply passes the resource storage to a command.
    """
    # Wraps here makes sure the original docstring propagates to click
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(resource_storage=env.resource_storage, *args, **kwargs)

    return wrapper


def pass_context(func):
    """
    Make click context ARIA specific.

    This exists purely for aesthetic reasons, otherwise some decorators are called
    ``@click.something`` instead of ``@aria.something``.
    """
    return click.pass_context(func)


class AliasedGroup(click.Group):
    def __init__(self, *args, **kwargs):
        self.max_suggestions = kwargs.pop("max_suggestions", 3)
        self.cutoff = kwargs.pop("cutoff", 0.5)
        super(AliasedGroup, self).__init__(*args, **kwargs)

    def get_command(self, ctx, cmd_name):
        cmd = click.Group.get_command(self, ctx, cmd_name)
        if cmd is not None:
            return cmd
        matches = \
            [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: {0}'.format(', '.join(sorted(matches))))

    def resolve_command(self, ctx, args):
        """
        Override clicks ``resolve_command`` method
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
                error_msg += '{0}{0}Did you mean one of these?{0}    {1}'.format(
                    os.linesep,
                    '{0}    '.format(os.linesep).join(matches, ))
            raise click.exceptions.UsageError(error_msg, error.ctx)


def group(name):
    """
    Allow to create a group with a default click context and a cls for click's ``didyoueamn``
    without having to repeat it for every group.
    """
    return click.group(
        name=name,
        context_settings=CLICK_CONTEXT_SETTINGS,
        cls=AliasedGroup)


def command(*args, **kwargs):
    """
    Make Click commands ARIA specific.

    This exists purely for aesthetic reasons, otherwise some decorators are called
    ``@click.something`` instead of ``@aria.something``.
    """
    return click.command(*args, **kwargs)


def argument(*args, **kwargs):
    """
    Make Click arguments ARIA specific.

    This exists purely for aesthetic reasons, otherwise some decorators are called
    ``@click.something`` instead of ``@aria.something``
    """
    return click.argument(*args, **kwargs)


class Options(object):
    def __init__(self):
        """
        The options API is nicer when you use each option by calling ``@aria.options.some_option``
        instead of ``@aria.some_option``.

        Note that some options are attributes and some are static methods. The reason for that is
        that we want to be explicit regarding how a developer sees an option. If it can receive
        arguments, it's a method - if not, it's an attribute.
        """
        self.version = click.option(
            '--version',
            is_flag=True,
            callback=show_version,
            expose_value=False,
            is_eager=True,
            help=helptexts.VERSION)

        self.json_output = click.option(
            '--json-output',
            is_flag=True,
            help=helptexts.JSON_OUTPUT)

        self.dry_execution = click.option(
            '--dry',
            is_flag=True,
            help=helptexts.DRY_EXECUTION)

        self.reset_config = click.option(
            '--reset-config',
            is_flag=True,
            help=helptexts.RESET_CONFIG)

        self.descending = click.option(
            '--descending',
            required=False,
            is_flag=True,
            default=defaults.SORT_DESCENDING,
            help=helptexts.DESCENDING)

        self.service_template_filename = click.option(
            '-n',
            '--service-template-filename',
            default=defaults.SERVICE_TEMPLATE_FILENAME,
            help=helptexts.SERVICE_TEMPLATE_FILENAME)

        self.service_template_mode_full = mutually_exclusive_option(
            '-f',
            '--full',
            'mode_full',
            mutually_exclusive=('mode_types',),
            is_flag=True,
            help=helptexts.SHOW_FULL,
            mutuality_description='-t, --types',
            mutuality_error=helptexts.MODE_MUTUALITY_ERROR_MESSAGE)

        self.service_mode_full = mutually_exclusive_option(
            '-f',
            '--full',
            'mode_full',
            mutually_exclusive=('mode_graph',),
            is_flag=True,
            help=helptexts.SHOW_FULL,
            mutuality_description='-g, --graph',
            mutuality_error=helptexts.MODE_MUTUALITY_ERROR_MESSAGE)

        self.mode_types = mutually_exclusive_option(
            '-t',
            '--types',
            'mode_types',
            mutually_exclusive=('mode_full',),
            is_flag=True,
            help=helptexts.SHOW_TYPES,
            mutuality_description='-f, --full',
            mutuality_error=helptexts.MODE_MUTUALITY_ERROR_MESSAGE)

        self.mode_graph = mutually_exclusive_option(
            '-g',
            '--graph',
            'mode_graph',
            mutually_exclusive=('mode_full',),
            is_flag=True,
            help=helptexts.SHOW_GRAPH,
            mutuality_description='-f, --full',
            mutuality_error=helptexts.MODE_MUTUALITY_ERROR_MESSAGE)

        self.format_json = mutually_exclusive_option(
            '-j',
            '--json',
            'format_json',
            mutually_exclusive=('format_yaml',),
            is_flag=True,
            help=helptexts.SHOW_JSON,
            mutuality_description='-y, --yaml',
            mutuality_error=helptexts.FORMAT_MUTUALITY_ERROR_MESSAGE)

        self.format_yaml = mutually_exclusive_option(
            '-y',
            '--yaml',
            'format_yaml',
            mutually_exclusive=('format_json',),
            is_flag=True,
            help=helptexts.SHOW_YAML,
            mutuality_description='-j, --json',
            mutuality_error=helptexts.FORMAT_MUTUALITY_ERROR_MESSAGE)

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
    def inputs(help):
        return click.option(
            '-i',
            '--inputs',
            multiple=True,
            callback=inputs_callback,
            help=help)

    @staticmethod
    def force(help):
        return click.option(
            '-f',
            '--force',
            is_flag=True,
            help=help)

    @staticmethod
    def task_max_attempts(default=defaults.TASK_MAX_ATTEMPTS):
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
    def task_retry_interval(default=defaults.TASK_RETRY_INTERVAL):
        return click.option(
            '--task-retry-interval',
            type=int,
            default=default,
            help=helptexts.TASK_RETRY_INTERVAL.format(default))

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

    @staticmethod
    def mark_pattern():
        return click.option(
            '-m',
            '--mark-pattern',
            help=helptexts.MARK_PATTERN,
            type=str,
            required=False
        )

options = Options()
