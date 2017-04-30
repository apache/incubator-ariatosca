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

import requests

from .testenv import testenv  # pylint: disable=unused-import
from .. import helpers


def test_hello_world(testenv):
    hello_world_template_uri = helpers.get_example_uri('hello-world', 'helloworld.yaml')
    service_name = testenv.install_service(hello_world_template_uri)

    try:
        _verify_deployed_service_in_storage(service_name, testenv.model_storage)
        _verify_webserver_up('http://localhost:9090')
    finally:
        # Even if some assertions failed, attempt to execute uninstall so the
        # webserver process doesn't stay up once the test is finished
        testenv.uninstall_service()

    _verify_webserver_down('http://localhost:9090')
    testenv.verify_clean_storage()


def _verify_webserver_up(http_endpoint):
    server_response = requests.get(http_endpoint, timeout=10)
    assert server_response.status_code == 200


def _verify_webserver_down(http_endpoint):
    try:
        requests.get(http_endpoint, timeout=10)
        assert False
    except requests.exceptions.ConnectionError:
        pass


def _verify_deployed_service_in_storage(service_name, model_storage):
    service_templates = model_storage.service_template.list()
    assert len(service_templates) == 1
    assert len(service_templates[0].services) == 1
    service = service_templates[0].services[0]
    assert service.name == service_name
    assert len(service.executions) == 1
    assert len(service.nodes) == 2
    assert all(node.state == node.STARTED for node in service.nodes.values())
    assert len(service.executions[0].logs) > 0
