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

"""
ARIA API components required to handle user actions and expose functionality.
Implemented as `Command` pattern. Each `Command` represents single atomic action exposed by ARIA.
`Commands` may be run by `Invokers` and results of its execution may be gathered by `Receivers`.
`Invoker` and `Receiver` may be subclassed to expose ARIA functionality by different kinds of API.
"""

import sys

from ..logger import LoggerMixin
from ..utils.exceptions import print_exception


class CommandNotFoundError(Exception):
    """
    Exception raised when there are not defined `Command` object to handle given user action.
    """
    pass


class InvalidCommandInputDataError(Exception):
    """
    Exception raised when input data for given `Command` object is invalid.
    """
    pass


class Command(LoggerMixin):
    """
    Base class represents single ARIA API action.
    """

    class InputData(object):
        """
        Base class represents single ARIA API action input data.
        Acts as a schema. Defined to enable commands reuse and API independence.
        """

        MANDATORY_FIELDS = []

        OPTIONAL_FIELDS = []

        def __init__(self, data, unknown_data):
            """
            :param data: dict with parameters required by given subclass
            :param unknown_data: list with additional data e.g. as result of parsing process
            """

            for field in self.MANDATORY_FIELDS:
                if field not in data.keys():
                    raise InvalidCommandInputDataError(
                        "Parameter {0} is required for command execution, but is not present"
                        .format(field)
                    )

                setattr(self, field, data.pop(field))

            for field in self.OPTIONAL_FIELDS:
                value = None

                if field in data.keys():
                    value = data.pop(field)

                setattr(self, field, value)

            self.unused_data = data
            self.unknown_data = unknown_data

    @classmethod
    def name(cls):
        """
        :return: name of `Command`. Necessary to enable commands registration
        and used to identify `Command` in user interface code.
        """

        return ""

    def __init__(self, receiver):
        """
        :param receiver: `Receiver` subclass instance,
        which is able to handle `Command` execution results.
        """
        super(Command, self).__init__()
        self.receiver = receiver

    def __repr__(self):
        return 'AriaCommand({cls.__name__})'.format(cls=self.__class__)

    def __call__(self, data, *args):
        """
        Entry point for each `Command` to run its execution.

        :param data: dict with parameters required by given `Command`
        :param args: list with additional data e.g. as result of parsing process
        """
        self.execute(self.__class__.InputData(data if isinstance(data, dict) else vars(data), args))

    def execute(self, command_data):
        """
        Abstract method defined to provide by each subclass command execution logic.

        :param command_data: `InputData` instance, defined for given `Command` subclass.
        """
        pass


class Receiver(LoggerMixin):
    """
    Base class for objects, which can handle `Command` execution result.
    """

    def receive(self, command_execution_result):
        pass


class StreamReceiver(Receiver):
    """
    Base `Receiver` class, which may be treat as stream
    """

    # It should be possible to treat StdOutReceiver as stream object
    def write(self, command_execution_result):
        self.receive(command_execution_result)


class StdOutReceiver(StreamReceiver):
    """
    `Receiver`, enables forwarding of `Command` execution result to standard output.
    """

    def __init__(self):
        super(StdOutReceiver, self).__init__()
        self.out = sys.stdout

    def receive(self, command_execution_result):
        self.out.write(str(command_execution_result))


class Invoker(LoggerMixin):
    """
    Core API class, used to process each user action by proper `Command` execution.
    """

    def __init__(self, *args, **kwargs):
        super(Invoker, self).__init__()
        self.commands = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Here we will handle errors
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        # TODO: error handling
        # TODO: cleanup if needed
        # TODO: user message if needed
        pass

    def register_command(self, command):
        """
        Registers single `Command`.
        After registration this `Command` will be available to be executed by user.

        :param command: `Command` instance to be registered
        """
        command_name = command.name()

        if command_name in self.commands.keys():
            self.logger.warn("Command {0} has been already registered".format(command_name))
            return

        command.with_logger(base_logger=self.logger)
        self.commands[command_name] = command
        self.logger.debug("Command {0} registered successfully".format(command_name))

    def register_commands(self, commands):
        """
        Registers multiple `Commands`.
        After registration these `Commands` will be available to be executed by user.

        :param commands: list of `Command` instances to be registered
        """

        for command in commands:
            self.register_command(command)

    def execute(self, command_name, data, receiver, *args):
        """
        Entry point for handling single user action.
        Checks if has corresponding `Command` already registered and next executes it.

        :param command_name: name of `Command` to be executed
        :param data: dict with parameters required by given `Command`
        :param receiver: receiver object responsible in handling execution result
        :param args: additional parameters
        """
        command = self.commands[command_name]

        if not command:
            raise CommandNotFoundError("Command {0} not found".format(command))

        self.logger.info('Running command: {0}'.format(command))

        try:
            command(receiver)(data, *args)
        except Exception as e:
            print_exception(e)


class DefaultInvoker(Invoker):
    """
    `Invoker` class, containing basic ARIA `Commands`
    (functionalities) registered and available to user.
    """
    from .commands import (
        ParseCommand,
        WorkflowCommand,
        InitCommand,
        ExecuteCommand,
        CSARCreateCommand,
        CSAROpenCommand,
        CSARValidateCommand,
        SpecCommand
    )

    DEFAULT_COMMANDS = [
        ParseCommand,
        WorkflowCommand,
        InitCommand,
        ExecuteCommand,
        CSARCreateCommand,
        CSAROpenCommand,
        CSARValidateCommand,
        SpecCommand
    ]

    def __init__(self, *args, **kwargs):
        super(DefaultInvoker, self).__init__(*args, **kwargs)
        self.register_commands(self.DEFAULT_COMMANDS)


class Api(DefaultInvoker):
    """
    Class represents single User Interface.
    """

    def run(self):
        pass
