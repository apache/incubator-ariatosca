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
    'aria.interfaces.lifecycle.create',
    'aria.interfaces.lifecycle.configure',
    'aria.interfaces.lifecycle.start',
    ]
NODE_OPERATIONS_UNINSTALL = [
    'aria.interfaces.lifecycle.stop',
    'aria.interfaces.lifecycle.delete',
]
NODE_OPERATIONS = NODE_OPERATIONS_INSTALL + NODE_OPERATIONS_UNINSTALL

RELATIONSHIP_OPERATIONS_INSTALL = [
    'aria.interfaces.relationship_lifecycle.preconfigure',
    'aria.interfaces.relationship_lifecycle.postconfigure',
    'aria.interfaces.relationship_lifecycle.establish',
    ]
RELATIONSHIP_OPERATIONS_UNINSTALL = ['aria.interfaces.relationship_lifecycle.unlink']
RELATIONSHIP_OPERATIONS = RELATIONSHIP_OPERATIONS_INSTALL + RELATIONSHIP_OPERATIONS_UNINSTALL
