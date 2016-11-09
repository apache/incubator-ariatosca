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

from collections import OrderedDict

from ..utils import StrictDict, puts
from .utils import coerce_value


class Function(object):
    """
    An intrinsic function.

    Serves as a placeholder for a value that should eventually be derived
    by calling the function.
    """

    @property
    def as_raw(self):
        raise NotImplementedError

    def _evaluate(self, context, container):
        raise NotImplementedError

    def __deepcopy__(self, memo):
        # Circumvent cloning in order to maintain our state
        return self


class Element(object):
    """
    Base class for :class:`ServiceInstance` elements.

    All elements support validation, diagnostic dumping, and representation as
    raw data (which can be translated into JSON or YAML) via :code:`as_raw`.
    """

    @property
    def as_raw(self):
        raise NotImplementedError

    def validate(self, context):
        pass

    def coerce_values(self, context, container, report_issues):
        pass

    def dump(self, context):
        pass


class ModelElement(Element):
    """
    Base class for :class:`ServiceModel` elements.

    All model elements can be instantiated into :class:`ServiceInstance` elements.
    """

    def instantiate(self, context, container):
        raise NotImplementedError


class Parameter(ModelElement):
    """
    Represents a typed value.

    This class is used by both service model and service instance elements.
    """

    def __init__(self, type_name, value, description):
        self.type_name = type_name
        self.value = value
        self.description = description

    @property
    def as_raw(self):
        return OrderedDict((
            ('type_name', self.type_name),
            ('value', self.value),
            ('description', self.description)))

    def instantiate(self, context, container):
        return Parameter(self.type_name, self.value, self.description)

    def coerce_values(self, context, container, report_issues):
        if self.value is not None:
            self.value = coerce_value(context, container, self.value, report_issues)


class Metadata(ModelElement):
    """
    Custom values associated with the deployment template and its plans.

    This class is used by both service model and service instance elements.

    Properties:

    * :code:`values`: Dict of custom values
    """

    def __init__(self):
        self.values = StrictDict(key_class=basestring)

    @property
    def as_raw(self):
        return self.values

    def instantiate(self, context, container):
        metadata = Metadata()
        metadata.values.update(self.values)
        return metadata

    def dump(self, context):
        puts('Metadata:')
        with context.style.indent:
            for name, value in self.values.iteritems():
                puts('%s: %s' % (name, context.style.meta(value)))
