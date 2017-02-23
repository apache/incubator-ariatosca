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

from sqlalchemy import (
    Column,
    Text
)

from ..parser.modeling import utils
from ..storage import exceptions
from ..utils.collections import OrderedDict

from . import structure

# pylint: disable=no-self-argument, no-member, abstract-method


class ParameterBase(structure.TemplateModelMixin):
    """
    Represents a typed value.

    This class is used by both service template and service instance elements.
    """

    __tablename__ = 'parameter'

    name = Column(Text, nullable=False)
    type_name = Column(Text, nullable=False)

    # Check: value type
    str_value = Column(Text)
    description = Column(Text)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('value', self.value),
            ('description', self.description)))

    @property
    def value(self):
        if self.type_name is None:
            return
        try:
            if self.type_name.lower() in ('str', 'unicode'):
                return self.str_value.decode('utf-8')
            elif self.type_name.lower() == 'int':
                return int(self.str_value)
            elif self.type_name.lower() == 'bool':
                return bool(self.str_value)
            elif self.type_name.lower() == 'float':
                return float(self.str_value)
            else:
                return self.str_value
        except ValueError:
            raise exceptions.StorageError('Trying to cast {0} to {1} failed'.format(self.str_value,
                                                                                    self.type))

    @value.setter
    def value(self, value):
        self.str_value = unicode(value)

    def instantiate(self, context, container):
        from . import model
        return model.Parameter(type_name=self.type_name,
                               str_value=self.str_value,
                               description=self.description)

    def coerce_values(self, context, container, report_issues):
        if self.str_value is not None:
            self.str_value = utils.coerce_value(context, container, self.str_value, report_issues)


class MetadataBase(structure.TemplateModelMixin):
    """
    Custom values associated with the service.

    This class is used by both service template and service instance elements.
    """

    __tablename__ = 'metadata'

    name = Column(Text, nullable=False)
    value = Column(Text)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('value', self.value)))

    def instantiate(self, context, container):
        from . import model
        return model.Metadata(name=self.name,
                              value=self.value)
