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
ARIA modeling service changes module
"""

# pylint: disable=no-self-argument, no-member, abstract-method

from collections import namedtuple

from sqlalchemy import (
    Column,
    Text,
    DateTime,
    Enum,
)
from sqlalchemy.ext.declarative import declared_attr

from .types import (List, Dict)
from .mixins import ModelMixin
from . import relationship


class ServiceUpdateBase(ModelMixin):
    """
    Deployment update model representation.
    """
    __tablename__ = 'service_update'

    __private_fields__ = ('service_fk',
                          'execution_fk')

    created_at = Column(DateTime, nullable=False, index=True)
    service_plan = Column(Dict, nullable=False)
    service_update_nodes = Column(Dict)
    service_update_service = Column(Dict)
    service_update_node_templates = Column(List)
    modified_entity_ids = Column(Dict)
    state = Column(Text)

    # region association proxies

    @declared_attr
    def execution_name(cls):
        return relationship.association_proxy('execution', cls.name_column_name())

    @declared_attr
    def service_name(cls):
        return relationship.association_proxy('service', cls.name_column_name())

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def steps(cls):
        return relationship.one_to_many(cls, 'service_update_step')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def execution(cls):
        return relationship.one_to_one(cls, 'execution', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def service(cls):
        return relationship.many_to_one(cls, 'service', back_populates='updates')

    # endregion

    # region foreign keys

    @declared_attr
    def execution_fk(cls):
        return relationship.foreign_key('execution', nullable=True)

    @declared_attr
    def service_fk(cls):
        return relationship.foreign_key('service')

    # endregion

    def to_dict(self, suppress_error=False, **kwargs):
        dep_update_dict = super(ServiceUpdateBase, self).to_dict(suppress_error)     #pylint: disable=no-member
        # Taking care of the fact the DeploymentSteps are _BaseModels
        dep_update_dict['steps'] = [step.to_dict() for step in self.steps]
        return dep_update_dict


class ServiceUpdateStepBase(ModelMixin):
    """
    Deployment update step model representation.
    """

    __tablename__ = 'service_update_step'

    __private_fields__ = ('service_update_fk',)

    _action_types = namedtuple('ACTION_TYPES', 'ADD, REMOVE, MODIFY')
    ACTION_TYPES = _action_types(ADD='add', REMOVE='remove', MODIFY='modify')

    _entity_types = namedtuple(
        'ENTITY_TYPES',
        'NODE, RELATIONSHIP, PROPERTY, OPERATION, WORKFLOW, OUTPUT, DESCRIPTION, GROUP, PLUGIN')
    ENTITY_TYPES = _entity_types(
        NODE='node',
        RELATIONSHIP='relationship',
        PROPERTY='property',
        OPERATION='operation',
        WORKFLOW='workflow',
        OUTPUT='output',
        DESCRIPTION='description',
        GROUP='group',
        PLUGIN='plugin'
    )

    action = Column(Enum(*ACTION_TYPES, name='action_type'), nullable=False)
    entity_id = Column(Text, nullable=False)
    entity_type = Column(Enum(*ENTITY_TYPES, name='entity_type'), nullable=False)

    # region association proxies

    @declared_attr
    def service_update_name(cls):
        return relationship.association_proxy('service_update', cls.name_column_name())

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service_update(cls):
        return relationship.many_to_one(cls, 'service_update', back_populates='steps')

    # endregion

    # region foreign keys

    @declared_attr
    def service_update_fk(cls):
        return relationship.foreign_key('service_update')

    # endregion

    def __hash__(self):
        return hash((getattr(self, self.id_column_name()), self.entity_id))

    def __lt__(self, other):
        """
        the order is 'remove' < 'modify' < 'add'
        :param other:
        :return:
        """
        if not isinstance(other, self.__class__):
            return not self >= other

        if self.action != other.action:
            if self.action == 'remove':
                return_value = True
            elif self.action == 'add':
                return_value = False
            else:
                return_value = other.action == 'add'
            return return_value

        if self.action == 'add':
            return self.entity_type == 'node' and other.entity_type == 'relationship'
        if self.action == 'remove':
            return self.entity_type == 'relationship' and other.entity_type == 'node'
        return False


class ServiceModificationBase(ModelMixin):
    """
    Deployment modification model representation.
    """

    __tablename__ = 'service_modification'

    __private_fields__ = ('service_fk',)

    STARTED = 'started'
    FINISHED = 'finished'
    ROLLEDBACK = 'rolledback'

    STATES = [STARTED, FINISHED, ROLLEDBACK]
    END_STATES = [FINISHED, ROLLEDBACK]

    context = Column(Dict)
    created_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, index=True)
    modified_node_templates = Column(Dict)
    nodes = Column(Dict)
    status = Column(Enum(*STATES, name='service_modification_status'))

    # region association proxies

    @declared_attr
    def service_name(cls):
        return relationship.association_proxy('service', cls.name_column_name())

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service(cls):
        return relationship.many_to_one(cls, 'service', back_populates='modifications')

    # endregion

    # region foreign keys

    @declared_attr
    def service_fk(cls):
        return relationship.foreign_key('service')

    # endregion
