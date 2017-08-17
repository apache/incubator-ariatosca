# -*- coding: utf-8 -*-
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


def test_names_shorthand(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  node_templates:
    my_server:
      type: Compute
      requirements:
        - local_storage:
            node: my_block_storage
            relationship:
              type: AttachesTo
              properties:
                location: /path1/path2
    my_block_storage:
      type: BlockStorage
      properties:
        size: 10 GB
""", import_profile=True).assert_success()


def test_names_type_qualified(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  node_templates:
    my_server:
      type: tosca:Compute
      requirements:
        - local_storage:
            node: my_block_storage
            relationship:
              type: AttachesTo
              properties:
                location: /path1/path2
    my_block_storage:
      type: tosca:BlockStorage
      properties:
        size: 10 GB
""", import_profile=True).assert_success()
