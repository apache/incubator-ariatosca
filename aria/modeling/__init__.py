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
    base,
    type,
    model,
    service_template_models as _service_template_models_base,
    service_models as _service_models_base,
    orchestrator_models as _orchestrator_models_base,
)


_ModelBaseCls = namedtuple('ModelBase', 'service_template_models,'
                                        'service_models,'
                                        'orchestrator_models')
model_base = _ModelBaseCls(service_template_models=_service_template_models_base,
                           service_models=_service_models_base,
                           orchestrator_models=_orchestrator_models_base)
                           

__all__ = (
    'base',
    'type',
    'model',
    'model_base',
)
