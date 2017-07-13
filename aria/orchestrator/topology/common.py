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


class HandlerBase(object):
    def __init__(self, topology, model):
        self._topology = topology
        self._model = model

    def coerce(self, **kwargs):
        raise NotImplementedError

    def _coerce(self, *models, **kwargs):
        for template in models:
            self._topology.coerce(template, **kwargs)

    def validate(self, **kwargs):
        raise NotImplementedError

    def _validate(self, *models, **kwargs):
        for template in models:
            self._topology.validate(template, **kwargs)

    def dump(self, out_stream):
        raise NotImplementedError


class TemplateHandlerBase(HandlerBase):
    """
    Base handler for template based models
    """

    def instantiate(self, instance_cls, **kwargs):
        raise NotImplementedError


class InstanceHandlerBase(HandlerBase):
    """
    Base handler for instance based models

    """
    def validate(self, **kwargs):
        raise NotImplementedError

    def coerce(self, **kwargs):
        raise NotImplementedError

    def dump(self, out_stream):
        raise NotImplementedError


class ActorHandlerBase(HandlerBase):
    """
    Base handler for any model which has (or contains a field which references) an operation
    """
    def configure_operations(self):
        raise NotImplementedError
