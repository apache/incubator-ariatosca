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

from .service_templates import (consume_use_case, consume_node_cellar)


# Use Cases

def test_use_case_compute_1():
    consume_use_case('compute-1', 'instance')


def test_use_case_software_component_1():
    consume_use_case('software-component-1', 'instance')


def test_use_case_block_storage_1():
    consume_use_case('block-storage-1', 'instance')


def test_use_case_block_storage_2():
    consume_use_case('block-storage-2', 'instance')


def test_use_case_block_storage_3():
    consume_use_case('block-storage-3', 'instance')


def test_use_case_block_storage_4():
    consume_use_case('block-storage-4', 'instance')


def test_use_case_block_storage_5():
    consume_use_case('block-storage-5', 'instance')


def test_use_case_block_storage_6():
    consume_use_case('block-storage-6', 'instance')


def test_use_case_object_storage_1():
    consume_use_case('object-storage-1', 'instance')


def test_use_case_network_1():
    consume_use_case('network-1', 'instance')


def test_use_case_network_2():
    consume_use_case('network-2', 'instance')


def test_use_case_network_3():
    consume_use_case('network-3', 'instance')


def test_use_case_network_4():
    consume_use_case('network-4', 'instance')


def test_use_case_webserver_dbms_1():
    consume_use_case('webserver-dbms-1', 'template')


def test_use_case_webserver_dbms_2():
    consume_use_case('webserver-dbms-2', 'instance')


def test_use_case_multi_tier_1():
    consume_use_case('multi-tier-1', 'instance')


def test_use_case_container_1():
    consume_use_case('container-1', 'template')


# NodeCellar

def test_node_cellar_validation():
    consume_node_cellar('validate')


def test_node_cellar_validation_no_cache():
    consume_node_cellar('validate', False)


def test_node_cellar_presentation():
    consume_node_cellar('presentation')


def test_node_cellar_model():
    consume_node_cellar('template')


def test_node_cellar_types():
    consume_node_cellar('types')


def test_node_cellar_instance():
    consume_node_cellar('instance')
