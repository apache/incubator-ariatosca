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

from mock import (
    MagicMock,
    Mock
    )
import pytest
from aria_service_proxy import tasks
from cloudify.exceptions import NonRecoverableError
from cloudify.state import current_ctx


# Tests that a retry is performed when wait_for_service is true and
# the service doesn't exist
def test_noservice_with_wait(monkeypatch):
    node = Mock(properties={'service_name': 'testwait',
                            'wait_config':
                            {'wait_for_service': True, 'wait_time': 5},
                            'outputs': ['someoutput']})
    attrs = {'retry.return_value': 'retry'}
    operation = Mock(retry_number=0, **attrs)
    ctxmock = MagicMock(node = node, operation = operation)
    current_ctx.set(ctxmock)
    monkeypatch.setattr(tasks,"get_service_names",lambda: {})
    ret = tasks.proxy_connect()
    assert(ret == 'retry')


# Make sure error raised when no service exists and no wait is configured
def test_noservice_no_wait(monkeypatch):
    node = Mock(properties={'service_name': 'testfail',
                              'wait_config': {'wait_for_service': False, 'wait_time': 5 },
                              'outputs': ['someoutput']})
    ctxmock = MagicMock(node = node)
    current_ctx.set(ctxmock)
    monkeypatch.setattr(tasks,"get_service_names",lambda: {})
    with pytest.raises(NonRecoverableError):
        tasks.proxy_connect()


# Test that a service for which wait is specified, is retried
# properly, and the retry results in success after the service
# appears
def test_service_eventual_complete(monkeypatch):
    output = Mock( value = 'someval')
    service = Mock(outputs = { 'someoutput': output })

    node = Mock( properties = {
                      'service_name': 'test',
                      'wait_config': { 'wait_for_service':True,
                                       'wait_time': 1 },
                      'outputs':['someoutput']
                      }
               )

    instance = Mock(runtime_properties = {})
    attrs = {'retry.return_value' : 'retry' }
    operation = Mock( retry_number = 0, **attrs)
    ctxmock = MagicMock( node = node , operation = operation, instance = instance)
    current_ctx.set(ctxmock)
    monkeypatch.setattr(tasks, "get_service_names", lambda: {'test': service })
    monkeypatch.setattr(tasks, "is_installed", lambda a: False)

    ret = tasks.proxy_connect()
    assert(ret == 'retry')

    monkeypatch.setattr(tasks, "get_service_names", lambda: {'test': service })
    monkeypatch.setattr(tasks, "is_installed", lambda a: True)
    ret = tasks.proxy_connect()
    assert(ret == None)
    assert(len(ctxmock.instance.runtime_properties['service_outputs']) == 1)
    assert(ctxmock.instance.runtime_properties['service_outputs'][0]['name'] == 'someoutput')
    assert(ctxmock.instance.runtime_properties['service_outputs'][0]['value'] == 'someval')


# Test that a proxy generates a retry when the service exists, but the
# outputs don't, and wait is configured
def test_output_retry(monkeypatch):
    output = Mock( value = 'someval')
    service = Mock(outputs= {'test':output})
    node = Mock(properties = {'service_name': 'test',
                              'wait_config':
                              {'wait_for_service': True, 'wait_time':5},
                              'outputs': ['someoutput']})
    attrs = {'retry.return_value' : 'retry' }
    operation = Mock( retry_number = 0, **attrs)
    ctxmock = MagicMock( node = node , operation = operation)
    current_ctx.set(ctxmock)
    monkeypatch.setattr(tasks, "get_service_names", lambda: {'test': service})
    monkeypatch.setattr(tasks, "is_installed", lambda a: True)

    ret = tasks.proxy_connect()
    assert(ret == 'retry')


# Test that nominal path works: service complete, outputs available
def test_output_complete(monkeypatch):
    output = Mock( value = 'someval')
    service = Mock(outputs= {'someoutput':output})
    node = Mock(properties = {'service_name': 'test',
                              'wait_config':{'wait_for_service': True, 'wait_time':5},
                              'outputs': ['someoutput']})
    attrs = {'retry.return_value' : 'retry' }
    operation = Mock( retry_number = 5, **attrs)
    ctxmock = MagicMock( node = node , operation = operation)
    current_ctx.set(ctxmock)
    monkeypatch.setattr(tasks, "get_service_names", lambda: {'test':service})
    monkeypatch.setattr(tasks, "is_installed", lambda a: True)

    ret = tasks.proxy_connect()
    assert(ret == None)

# Test that retry occurs propertly when outputs unavailable (and wait
# configured), and that they are propertly detected when they appear.
def test_output_eventual_complete(monkeypatch):
    output = Mock( value = 'someval')
    service = Mock(outputs= {'test':output})
    node = Mock(properties = {'service_name': 'test',
                              'wait_config':{'wait_for_service': True, 'wait_time':1},
                              'outputs': ['someoutput']})
    attrs = {'retry.return_value' : 'retry' }
    instance = Mock(runtime_properties = {})
    operation = Mock( retry_number = 0, **attrs)
    ctxmock = MagicMock( node = node , operation = operation, instance = instance)
    current_ctx.set(ctxmock)
    monkeypatch.setattr(tasks, "is_installed", lambda a: True)
    monkeypatch.setattr(tasks, "get_service_names", lambda: {'test':service})

    ret = tasks.proxy_connect()
    assert(ret == 'retry')

    service = Mock(outputs= {'someoutput':output})
    monkeypatch.setattr(tasks, "get_service_names", lambda: {'test':service})
    ret = tasks.proxy_connect()
    assert(ret == None)
    assert(len(ctxmock.instance.runtime_properties['service_outputs']) == 1)
    assert(ctxmock.instance.runtime_properties['service_outputs'][0]['name'] == 'someoutput')
    assert(ctxmock.instance.runtime_properties['service_outputs'][0]['value'] == 'someval')

# Test wait expression fuctionality for failure case.  Pass in an output
# with and test for incorrect length.  Should raise error.
def test_expr_fail(monkeypatch):
    output = Mock( value = 'someval')
    service = Mock(outputs= {'someoutput':output})
    node = Mock(properties = {'service_name': 'test',
                              'wait_config':
                                {'wait_for_service': True,
                                 'wait_expression': 'len(someoutput) == 1',
                                 'wait_time':5},
                              'outputs': ['someoutput']})
    attrs = {'retry.return_value' : 'retry' }
    operation = Mock( retry_number = 5, **attrs)
    ctxmock = MagicMock( node = node , operation = operation)
    current_ctx.set(ctxmock)
    monkeypatch.setattr(tasks, "get_service_names", lambda: {'test':service})
    monkeypatch.setattr(tasks, "is_installed", lambda a: True)

    with pytest.raises(NonRecoverableError):
        tasks.proxy_connect()

# Test wait expression fuctionality for success case.  Pass in an output
# with and test for correct length.  Should raise no error.
def test_expr_succeed(monkeypatch):
    output = Mock( value = 'someval')
    service = Mock(outputs= {'someoutput':output})
    node = Mock(properties = {'service_name': 'test',
                              'wait_config':
                                {'wait_for_service': True,
                                 'wait_expression': 'len(someoutput) == 7',
                                 'wait_time':5},
                              'outputs': ['someoutput']})
    attrs = {'retry.return_value' : 'retry' }
    operation = Mock( retry_number = 5, **attrs)
    ctxmock = MagicMock( node = node , operation = operation)
    current_ctx.set(ctxmock)
    monkeypatch.setattr(tasks, "get_service_names", lambda: {'test':service})
    monkeypatch.setattr(tasks, "is_installed", lambda a: True)

    ret = tasks.proxy_connect()
    assert(ret == None)

# Test wait expression fuctionality for success case using two outputs.
# Expression is boolean expression involving two outputs, and it true.
# Should raise no error.
def test_expr_succeed_mult(monkeypatch):
    output1 = Mock( value = 4)
    output2 = Mock( value = 7)
    service = Mock(outputs= {'o1':output1, 'o2': output2})
    node = Mock(properties = {'service_name': 'test',
                              'wait_config':
                                {'wait_for_service': True,
                                 'wait_expression': 'o1 < o2',
                                 'wait_time':5},
                              'outputs': ['o1','o2']})
    attrs = {'retry.return_value' : 'retry' }
    operation = Mock( retry_number = 5, **attrs)
    ctxmock = MagicMock( node = node , operation = operation)
    current_ctx.set(ctxmock)
    monkeypatch.setattr(tasks, "get_service_names", lambda: {'test':service})
    monkeypatch.setattr(tasks, "is_installed", lambda a: True)

    ret = tasks.proxy_connect()
    assert(ret == None)
