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
import os
import platform
from shutil import rmtree
from tempfile import mkdtemp

from sqlalchemy import (
    create_engine,
    orm,
    Column,
    Text,
    Integer,
    pool
)


from aria.modeling import (
    models,
    types as modeling_types,
    bases
)
from aria import modeling


class MockModel(models.aria_declarative_base, bases.ModelMixin): #pylint: disable=abstract-method
    __tablename__ = 'mock_model'
    model_dict = Column(modeling_types.Dict)
    model_list = Column(modeling_types.List)
    value = Column(Integer)
    name = Column(Text)


class TestFileSystem(object):

    def setup_method(self):
        self.path = mkdtemp('{0}'.format(self.__class__.__name__))

    def teardown_method(self):
        rmtree(self.path, ignore_errors=True)


def release_sqlite_storage(storage):
    """
    Drops the tables and clears the session
    :param storage:
    :return:
    """
    mapis = storage.registered.values()

    if mapis:
        for session in set(mapi._session for mapi in mapis):
            session.rollback()
            session.close()
        for engine in set(mapi._engine for mapi in mapis):
            models.aria_declarative_base.metadata.drop_all(engine)


def init_inmemory_model_storage():
    uri = 'sqlite:///:memory:'
    engine_kwargs = dict(connect_args={'check_same_thread': False}, poolclass=pool.StaticPool)

    engine = create_engine(uri, **engine_kwargs)
    session_factory = orm.sessionmaker(bind=engine)
    session = session_factory()

    return dict(engine=engine, session=session)
