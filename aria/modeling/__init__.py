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
    bases,
    types,
    models,
    service_template as _service_template_bases,
    service as _service_bases,
    orchestration as _orchestration_bases,
)


_ModelBasesCls = namedtuple('ModelBase', 'service_template,'
                                         'service,'
                                         'orchestration')

model_bases = _ModelBasesCls(service_template=_service_template_bases,
                             service=_service_bases,
                             orchestration=_orchestration_bases)


__all__ = (
    'bases',
    'types',
    'models',
    'model_bases',
)
