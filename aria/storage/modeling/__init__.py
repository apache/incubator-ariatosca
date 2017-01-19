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

from collections import namedtuple

from . import (
    model,
    instance_elements as _instance_base,
    orchestrator_elements as _orchestrator_base,
    template_elements as _template_base,
)

_ModelBaseCls = namedtuple('ModelBase', 'instance_elements,'
                                        'orchestrator_elements,'
                                        'template_elements')
model_base = _ModelBaseCls(instance_elements=_instance_base,
                           orchestrator_elements=_orchestrator_base,
                           template_elements=_template_base)

__all__ = (
    'model',
    'model_base',
)
