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
Mechanism for registering and loading ARIA extensions.
"""

# pylint: disable=no-self-use

from .utils import collections


class _Registrar(object):

    def __init__(self, registry):
        if not isinstance(registry, (dict, list)):
            raise RuntimeError('Unsupported registry type')
        self._registry = registry

    def register(self, function):
        result = function()
        if isinstance(self._registry, dict):
            for key in result:
                if key in self._registry:
                    raise RuntimeError('Re-definition of {0} in {1}'.format(key, function.__name__))
            self._registry.update(result)
        elif isinstance(self._registry, list):
            if not isinstance(result, (list, tuple, set)):
                result = [result]
            self._registry += list(result)
        else:
            raise RuntimeError('Illegal state')

    def __call__(self):
        return self._registry


def _registrar(function):
    function._registrar_function = True
    return function


class _ExtensionRegistration(object):
    """
    Base class for extension class decorators.
    """

    def __init__(self):
        self._registrars = {}
        self._registered_classes = []
        for attr, value in vars(self.__class__).items():
            try:
                is_registrar_function = value._registrar_function
            except AttributeError:
                is_registrar_function = False
            if is_registrar_function:
                registrar = _Registrar(registry=getattr(self, attr)())
                setattr(self, attr, registrar)
                self._registrars[attr] = registrar

    def __call__(self, cls):
        self._registered_classes.append(cls)
        return cls

    def init(self):
        """
        Initialize all registrars by calling all registered functions.
        """
        registered_instances = [cls() for cls in self._registered_classes]
        for name, registrar in self._registrars.items():
            for instance in registered_instances:
                registrating_function = getattr(instance, name, None)
                if registrating_function:
                    registrar.register(registrating_function)


class _ParserExtensionRegistration(_ExtensionRegistration):
    """
    Parser extensions class decorator.
    """

    @_registrar
    def presenter_class(self):
        """
        Presentation class registration.

        Implementing functions can return a single class or a list/tuple of classes.
        """
        return []

    @_registrar
    def specification_package(self):
        """
        Specification package registration.

        Implementing functions can return a package name or a list/tuple of names.
        """
        return []

    @_registrar
    def specification_url(self):
        """
        Specification URL registration.

        Implementing functions should return a dictionary from names to URLs.
        """
        return {}

    @_registrar
    def uri_loader_prefix(self):
        """
        URI loader prefix registration.

        Implementing functions can return a single prefix or a list/tuple of prefixes.
        """
        return collections.StrictList(value_class=basestring)

parser = _ParserExtensionRegistration()


class _ProcessExecutorExtensionRegistration(_ExtensionRegistration):
    """
    Process executor extension class decorator.
    """

    @_registrar
    def decorate(self):
        """
        The operation function executed by the process executor will be decorated with the function
        returned from ``decorate()``.
        """
        return []

process_executor = _ProcessExecutorExtensionRegistration()


def init():
    """
    Initialize all registrars by calling all registered functions.
    """
    parser.init()
    process_executor.init()
