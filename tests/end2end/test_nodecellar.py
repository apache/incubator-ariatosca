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

from .testenv import testenv  # pylint: disable=unused-import
from .. import helpers


def test_nodecellar(testenv):
    nodecellar_template_uri = helpers.get_service_template_uri(
        'tosca-simple-1.0', 'node-cellar', 'node-cellar.yaml')

    service_name = testenv.install_service(nodecellar_template_uri, dry=True)
    _verify_deployed_service_in_storage(service_name, testenv.model_storage)

    # testing dry execution of custom workflows
    testenv.execute_workflow(service_name, 'maintenance_on', dry=True)
    testenv.execute_workflow(service_name, 'maintenance_off', dry=True)

    testenv.uninstall_service(dry=True)
    testenv.verify_clean_storage()


def _verify_deployed_service_in_storage(service_name, model_storage):
    service_templates = model_storage.service_template.list()
    assert len(service_templates) == 1
    assert len(service_templates[0].services) == 1
    service = service_templates[0].services[service_name]
    assert service.name == service_name
    assert len(service.executions) == 0  # dry executions leave no traces
    assert len(service.nodes) == 15
