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

import collections

from ...utils.imports import import_fullname
from .consumer import ConsumerChain
from .inputs import Inputs
from .modeling import Instance, Model, Types
from .presentation import Read
from .validation import Validate


class ConsumerChainBuilder(object):
    """
    Builder for ConsumerChain.
    """

    VALIDATION_CHAIN_KEYWORD = 'validate'
    MODEL_CHAIN_KEYWORD = 'model'
    TYPES_CHAIN_KEYWORD = 'types'
    INSTANCE_CHAIN_KEYWORD = 'instance'

    CHAIN_COMPONENTS = collections.OrderedDict()
    CHAIN_COMPONENTS[VALIDATION_CHAIN_KEYWORD] = (Read, Validate)
    CHAIN_COMPONENTS[MODEL_CHAIN_KEYWORD] = (Model,)
    CHAIN_COMPONENTS[TYPES_CHAIN_KEYWORD] = (Types,)
    CHAIN_COMPONENTS[INSTANCE_CHAIN_KEYWORD] = (Inputs, Instance)

    def __init__(self, consumer=INSTANCE_CHAIN_KEYWORD, **kwargs):
        """
        :param consumer - keyword related to / name of last Consumer in chain
        """

        self.consumers = self._get_consumers(consumer)

    def _get_consumers(self, consumer_name):
        consumers = []

        for keyword, available_consumers in self.CHAIN_COMPONENTS.items():
            consumers.extend(available_consumers)

            if keyword == consumer_name:
                return consumers

        if consumer_name:
            consumers.append(import_fullname(consumer_name))

        return consumers

    def build(self, context):
        """
        Build chain

        :param context - ConsumptionContext object
        :return ConsumerChain
        """

        return ConsumerChain(context, self.consumers)
