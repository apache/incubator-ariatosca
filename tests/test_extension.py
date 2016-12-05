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

import pytest

from aria import extension

# #pylint: disable=no-member,no-method-argument,unused-variable


class TestRegistrar(object):

    def test_list_based_registrar_with_single_element_registration(self):
        class ExtensionRegistration(extension._ExtensionRegistration):
            @extension._registrar
            def list_based_registrar(*_):
                return []
        extension_registration = ExtensionRegistration()

        @extension_registration
        class Extension(object):
            def list_based_registrar(self):
                return True

        assert extension_registration.list_based_registrar() == []
        extension_registration.init()
        assert extension_registration.list_based_registrar() == [True]

    def test_list_based_registrar_with_sequence_element_registration(self):
        class ExtensionRegistration(extension._ExtensionRegistration):
            @extension._registrar
            def list_based_registrar1(*_):
                return []

            @extension._registrar
            def list_based_registrar2(*_):
                return []

            @extension._registrar
            def list_based_registrar3(*_):
                return []
        extension_registration = ExtensionRegistration()

        @extension_registration
        class Extension(object):
            def list_based_registrar1(*_):
                return [True, True]

            def list_based_registrar2(*_):
                return True, True

            def list_based_registrar3(*_):
                return set([True])

        extension_registration.init()
        assert extension_registration.list_based_registrar1() == [True, True]
        assert extension_registration.list_based_registrar2() == [True, True]
        assert extension_registration.list_based_registrar3() == [True]

    def test_dict_based_registrar(self):
        class ExtensionRegistration(extension._ExtensionRegistration):
            @extension._registrar
            def dict_based_registrar(*_):
                return {}
        extension_registration = ExtensionRegistration()

        @extension_registration
        class Extension1(object):
            def dict_based_registrar(self):
                return {
                    'a': 'a',
                    'b': 'b'
                }

        @extension_registration
        class Extension2(object):
            def dict_based_registrar(self):
                return {
                    'c': 'c',
                    'd': 'd'
                }

        assert extension_registration.dict_based_registrar() == {}
        extension_registration.init()
        assert extension_registration.dict_based_registrar() == {
            'a': 'a',
            'b': 'b',
            'c': 'c',
            'd': 'd'
        }

    def test_invalid_duplicate_key_dict_based_registrar(self):
        class ExtensionRegistration(extension._ExtensionRegistration):
            @extension._registrar
            def dict_based_registrar(*_):
                return {}
        extension_registration = ExtensionRegistration()

        @extension_registration
        class Extension1(object):
            def dict_based_registrar(self):
                return {
                    'a': 'val1',
                }

        @extension_registration
        class Extension2(object):
            def dict_based_registrar(self):
                return {
                    'a': 'val2',
                }

        with pytest.raises(RuntimeError):
            extension_registration.init()

    def test_unsupported_registrar(self):
        with pytest.raises(RuntimeError):
            class ExtensionRegistration(extension._ExtensionRegistration):
                @extension._registrar
                def unsupported_registrar(*_):
                    return set()
            extension_registration = ExtensionRegistration()

            @extension_registration
            class Extension(object):
                def unsupported_registrar(self):
                    return True

            extension_registration.init()

    def test_unimplemented_registration(self):
        class ExtensionRegistration(extension._ExtensionRegistration):
            @extension._registrar
            def list_based_registrar(*_):
                return []
        extension_registration = ExtensionRegistration()

        @extension_registration
        class Extension(object):
            pass

        assert extension_registration.list_based_registrar() == []
        extension_registration.init()
        assert extension_registration.list_based_registrar() == []
