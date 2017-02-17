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
from ..utils.collections import OrderedDict
from ..utils.console import puts
from .. import exceptions

from . import structure
from . import type

# pylint: disable=no-self-argument, no-member, abstract-method


class ParameterBase(structure.ModelMixin):
    """
    Represents a typed value.

    This class is used by both service model and service instance elements.
    """
    __tablename__ = 'parameter'
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False)

    # Check: value type
    str_value = Column(Text)
    description = Column(Text)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type),
            ('value', self.value),
            ('description', self.description)))

    @property
    def value(self):
        if self.type is None:
            return
        try:
            if self.type.lower() in ('str', 'unicode'):
                return self.str_value.decode('utf-8')
            elif self.type.lower() == 'int':
                return int(self.str_value)
            elif self.type.lower() == 'bool':
                return bool(self.str_value)
            elif self.type.lower() == 'float':
                return float(self.str_value)
            else:
                raise exceptions.StorageError('No supported type_name was provided')
        except ValueError:
            raise exceptions.StorageError('Trying to cast {0} to {1} failed'.format(self.str_value,
                                                                                    self.type))

    def instantiate(self, context, container):
        return ParameterBase(self.type, self.str_value, self.description)

    def coerce_values(self, context, container, report_issues):
        if self.str_value is not None:
            self.str_value = utils.coerce_value(context, container, self.str_value, report_issues)


class MetadataBase(structure.ModelMixin):
    """
    Custom values associated with the deployment template and its plans.

    This class is used by both service model and service instance elements.

    Properties:

    * :code:`values`: Dict of custom values
    """
    __tablename__ = 'metadata'
    values = Column(type.StrictDict(key_cls=basestring))

    @property
    def as_raw(self):
        return self.values

    def instantiate(self, context, container):
        metadata = MetadataBase()
        metadata.values.update(self.values)
        return metadata

    def dump(self, context):
        puts('Metadata:')
        with context.style.indent:
            for name, value in self.values.iteritems():
                puts('%s: %s' % (name, context.style.meta(value)))
