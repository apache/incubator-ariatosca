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
ARIA modeling type definition module
"""

# pylint: disable=too-many-lines, no-self-argument, no-member, abstract-method

from sqlalchemy import (
    Column,
    Text,
    DateTime,
    UniqueConstraint
)
from . import mixins

class TypeDefinitionBase(mixins.ModelMixin):
    """
    Loaded TypeDefinition.

    Usually created by various DSL parsers, such as ARIA's TOSCA extension. However, it can also be
    created programmatically.
    """

    __tablename__ = 'type_definition'

    name = Column(Text, nullable=False, index=True, doc="""
    Name of the type definition

    :type: :obj:`basestring`
    """)

    version = Column(Text, nullable=False, doc="""
    Version for the type definition

    :type: :obj:`basestring`
    """)

    main_file_name = Column(Text, nullable=False, doc="""
    Filename of CSAR or YAML file from which this type definition was parsed.

    :type: :obj:`basestring`
    """)

    uploaded_at = Column(DateTime, nullable=False, doc="""
    Timestamp for when the type definition was loaded.

    :type: :class:`~datetime.datetime`
    """)

    __table_args__ = (UniqueConstraint('name', 'version',
                                       name='_type_definition_name_version_unique'),)
