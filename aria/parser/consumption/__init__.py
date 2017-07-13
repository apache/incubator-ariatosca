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

"""
Consumption package.

.. autosummary::
   :nosignatures:

   aria.parser.consumption.ConsumptionContext

Consumers
---------

.. autosummary::
   :nosignatures:

   aria.parser.consumption.Consumer
   aria.parser.consumption.ConsumerChain
   aria.parser.consumption.ConsumerException
   aria.parser.consumption.Inputs
   aria.parser.consumption.ServiceTemplate
   aria.parser.consumption.Types
   aria.parser.consumption.CoerceServiceInstanceValues
   aria.parser.consumption.ValidateServiceInstance
   aria.parser.consumption.SatisfyRequirements
   aria.parser.consumption.ValidateCapabilities
   aria.parser.consumption.FindHosts
   aria.parser.consumption.ConfigureOperations
   aria.parser.consumption.ServiceInstance
   aria.parser.consumption.Read
   aria.parser.consumption.Validate
"""

from .exceptions import ConsumerException
from .context import ConsumptionContext
from .consumer import (
    Consumer,
    ConsumerChain
)
from .presentation import Read
from .validation import Validate
from .modeling import (
    ServiceTemplate,
    Types,
    ServiceInstance,
    FindHosts,
    ValidateServiceInstance,
    ConfigureOperations,
    SatisfyRequirements,
    ValidateCapabilities,
    CoerceServiceInstanceValues
)
from .inputs import Inputs

__all__ = (
    'ConsumerException',
    'ConsumptionContext',
    'Consumer',
    'ConsumerChain',
    'Read',
    'Validate',
    'ServiceTemplate',
    'Types',
    'ServiceInstance',
    'FindHosts',
    'ValidateServiceInstance',
    'ConfigureOperations',
    'SatisfyRequirements',
    'ValidateCapabilities',
    'CoerceServiceInstanceValues'
)
