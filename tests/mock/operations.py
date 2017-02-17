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

NODE_OPERATIONS_INSTALL = [
    ('Standard', 'create'),
    ('Standard', 'configure'),
    ('Standard', 'start')
]

NODE_OPERATIONS_UNINSTALL = [
    ('Standard', 'stop'),
    ('Standard', 'delete')
]

NODE_OPERATIONS = NODE_OPERATIONS_INSTALL + NODE_OPERATIONS_UNINSTALL

RELATIONSHIP_OPERATIONS_INSTALL = [
    ('Configure', 'pre_configure_source'),
    ('Configure', 'pre_configure_target'),
    ('Configure', 'add_source'),
    ('Configure', 'add_target')
]

RELATIONSHIP_OPERATIONS_UNINSTALL = [
    ('Configure', 'remove_target'),
    ('Configure', 'target_changed')
]

RELATIONSHIP_OPERATIONS = RELATIONSHIP_OPERATIONS_INSTALL + RELATIONSHIP_OPERATIONS_UNINSTALL

OPERATIONS_INSTALL = [
    ('Standard', 'create'),
    ('Configure', 'pre_configure_source'),
    ('Configure', 'pre_configure_target'),
    ('Standard', 'configure'),
    ('Standard', 'start'),
    ('Configure', 'add_source'),
    ('Configure', 'add_target'),
    ('Configure', 'target_changed')
]

OPERATIONS_UNINSTALL = [
    ('Configure', 'remove_target'),
    ('Configure', 'target_changed'),
    ('Standard', 'stop'),
    ('Standard', 'delete')
]
