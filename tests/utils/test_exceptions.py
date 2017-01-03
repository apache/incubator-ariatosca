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

import jsonpickle

from aria.utils import exceptions

_ARG1 = 'arg-1'
_ARG2 = 'arg-2'


class TestWrapIfNeeded(object):

    def test_no_wrapping_required1(self):
        e = JsonPickleableException1(_ARG1, _ARG2)
        assert exceptions.wrap_if_needed(e) is e

    def test_no_wrapping_required2(self):
        e = JsonPickleableException1(arg1=_ARG1, arg2=_ARG2)
        assert exceptions.wrap_if_needed(e) is e

    def test_no_wrapping_required3(self):
        e = JsonPickleableException2(arg1=_ARG1, arg2=_ARG2)
        assert exceptions.wrap_if_needed(e) is e

    def test_wrapping_required1(self):
        e = NonJsonPickleableException(_ARG1, _ARG2)
        wrapped_e = exceptions.wrap_if_needed(e)
        wrapped_e = jsonpickle.loads(jsonpickle.dumps(wrapped_e))
        assert isinstance(wrapped_e, exceptions._WrappedException)
        assert wrapped_e.exception_type == type(e).__name__
        assert wrapped_e.exception_str == str(e)

    def test_wrapping_required2(self):
        e = NonJsonPickleableException(arg1=_ARG1, arg2=_ARG2)
        wrapped_e = exceptions.wrap_if_needed(e)
        wrapped_e = jsonpickle.loads(jsonpickle.dumps(wrapped_e))
        assert isinstance(wrapped_e, exceptions._WrappedException)
        assert wrapped_e.exception_type == type(e).__name__
        assert wrapped_e.exception_str == str(e)


class JsonPickleableException1(Exception):
    def __init__(self, arg1, arg2):
        super(JsonPickleableException1, self).__init__(arg1, arg2)
        self.arg1 = arg1
        self.arg2 = arg2


class JsonPickleableException2(Exception):
    def __init__(self, arg1=None, arg2=None):
        super(JsonPickleableException2, self).__init__()
        self.arg1 = arg1
        self.arg2 = arg2


class NonJsonPickleableException(Exception):
    def __init__(self, arg1, arg2):
        super(NonJsonPickleableException, self).__init__()
        self.arg1 = arg1
        self.arg2 = arg2
