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
import threading

from ...utils.imports import import_fullname
from ..validation import ValidationContext
from ..loading import LoadingContext, UriLocation, LiteralLocation
from ..reading import ReadingContext
from ..presentation import PresentationContext
from ..modeling import ModelingContext
from .style import Style


_thread_locals = threading.local()


class ConsumptionContext(object):
    """
    Properties:

    * :code:`args`: The runtime arguments (usually provided on the command line)
    * :code:`out`: Message output stream (defaults to stdout)
    * :code:`style`: Message output style
    * :code:`validation`: :class:`aria.validation.ValidationContext`
    * :code:`loading`: :class:`aria.loading.LoadingContext`
    * :code:`reading`: :class:`aria.reading.ReadingContext`
    * :code:`presentation`: :class:`aria.presentation.PresentationContext`
    * :code:`modeling`: :class:`aria.service.ModelingContext`
    """

    @staticmethod
    def get_thread_local():
        """
        Gets the context attached to the current thread if there is one.
        """

        return getattr(_thread_locals, 'aria_consumption_context', None)

    def __init__(self, set_thread_local=True):
        self.args = []
        self.out = sys.stdout
        self.style = Style()
        self.validation = ValidationContext()
        self.loading = LoadingContext()
        self.reading = ReadingContext()
        self.presentation = PresentationContext()
        self.modeling = ModelingContext()

        if set_thread_local:
            self.set_thread_local()

    def set_thread_local(self):
        """
        Attaches this context to the current thread.
        """

        _thread_locals.aria_consumption_context = self

    def write(self, string):
        """
        Writes to our :code:`out`, making sure to encode UTF-8 if required.
        """

        try:
            self.out.write(string)
        except UnicodeEncodeError:
            self.out.write(string.encode('utf8'))

    def has_arg_switch(self, name):
        name = '--%s' % name
        return name in self.args

    def get_arg_value(self, name, default=None):
        name = '--%s=' % name
        for arg in self.args:
            if arg.startswith(name):
                return arg[len(name):]
        return default

    def get_arg_value_int(self, name, default=None):
        value = self.get_arg_value(name)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
        return default


class ConsumptionContextBuilder(object):
    """
    Builder for ConsumptionContext. Can be used to setup context for different usages.
    It takes dict of parameters describing context,
    passed via constructor and set corresponding context fields.

    Currently supported parameters:

    * :code:`loader_source`
    * :code:`reader_source`
    * :code:`presenter_source`
    * :code:`presenter`
    * :code:`out`
    * :code:`debug`
    * :code:`uri`
    * :code:`literal_location`
    * :code:`prefixes`
    """

    def __init__(self, *args, **kwargs):
        self.parameters = kwargs
        self.args = args

    def _set_when_defined(self,
                          object,
                          object_field_name,
                          parameters_field_name,
                          set_function,
                          instance=True):
        """
        Set `object_field_name` field in `object` using function `set_function`
        when parameter `parameters_field_name` is given.
        It can also create an instance when `set_function` is returning class.

        :param object - object, which field will be set
        :param object_field_name - name of `object` field, which will be set
        :param parameters_field_name - name of parameter,
        which value will be used to set object field
        :param set_function - function used to execute set operation,
        :param instance - if True creates new instance for result of `set_function` invocation.
        Default True
        """

        if parameters_field_name in self.parameters and self.parameters[parameters_field_name]:
            field_value = self.parameters[parameters_field_name]
            value_to_set = set_function(field_value)() if instance else set_function(field_value)

            setattr(object, object_field_name, value_to_set)

    def build(self):
        """
        Builds ConsumptionContext using predefined parameters set.
        """

        def set_uri(uri):
            return UriLocation(uri) if isinstance(uri, basestring) else uri

        def set_literal_location(literal_location):
            return LiteralLocation(literal_location)

        context = ConsumptionContext()
        context.args.extend(list(self.args))

        self._set_when_defined(
            context.loading, 'loader_source', 'loader_source', import_fullname)
        self._set_when_defined(
            context.reading, 'reader_source', 'reader_source', import_fullname)
        self._set_when_defined(
            context.presentation, 'presenter_source', 'presenter_source', import_fullname)
        self._set_when_defined(
            context.presentation, 'presenter_class', 'presenter', import_fullname)
        self._set_when_defined(
            context, 'out', 'out', lambda x: x, False)
        self._set_when_defined(
            context.presentation, 'print_exceptions', 'debug', lambda x: x, False)
        self._set_when_defined(
            context.presentation, 'location', 'uri', set_uri, False)
        self._set_when_defined(
            context.presentation, 'location', 'literal_location', set_literal_location, False)

        if 'inputs' in self.parameters:
            inputs = self.parameters['inputs']

            if inputs:
                if isinstance(inputs, dict):
                    for name, value in inputs.iteritems():
                        context.modeling.set_input(name, value)
                else:
                    context.args.append('--inputs=%s' % inputs)

        if 'prefixes' in self.parameters and self.parameters['prefixes']:
            context.loading.prefixes += [os.path.join(self.parameters['prefixes'], 'definitions')]

        return context
