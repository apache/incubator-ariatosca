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

from .service_templates import consume_test_case
from ..helpers import get_service_template_uri


def test_satisfy_capability_type():
    consume_reqs_caps_template1('instance')


def consume_reqs_caps_template1(consumer_class_name, cache=True):
    consume_test_case(
        get_service_template_uri('tosca-simple-1.0', 'reqs_caps', 'reqs_caps1.yaml'),
        consumer_class_name=consumer_class_name,
        cache=cache
    )
