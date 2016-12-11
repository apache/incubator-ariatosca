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
from tempfile import mkdtemp
from shutil import rmtree

from aria.storage import model
from sqlalchemy import (
    create_engine,
    orm)
from sqlalchemy.orm import scoped_session
from sqlalchemy.pool import StaticPool


class TestFileSystem(object):

    def setup_method(self):
        self.path = mkdtemp('{0}'.format(self.__class__.__name__))

    def teardown_method(self):
        rmtree(self.path, ignore_errors=True)


def get_sqlite_api_kwargs(base_dir=None, filename='db.sqlite'):
    """
    Create sql params. works in in-memory and in filesystem mode.
    If base_dir is passed, the mode will be filesystem mode. while the default mode is in-memory.
    :param str base_dir: The base dir for the filesystem memory file.
    :param str filename: the file name - defaults to 'db.sqlite'.
    :return:
    """
    if base_dir is not None:
        uri = 'sqlite:///{platform_char}{path}'.format(
            # Handles the windows behavior where there is not root, but drivers.
            # Thus behaving as relative path.
            platform_char='' if 'Windows' in platform.system() else '/',

            path=os.path.join(base_dir, filename))
        engine_kwargs = {}
    else:
        uri = 'sqlite:///:memory:'
        engine_kwargs = dict(connect_args={'check_same_thread': False},
                             poolclass=StaticPool)

    engine = create_engine(uri, **engine_kwargs)
    session_factory = orm.sessionmaker(bind=engine)
    session = scoped_session(session_factory=session_factory) if base_dir else session_factory()

    model.DeclarativeBase.metadata.create_all(bind=engine)
    return dict(engine=engine, session=session)


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
            model.DeclarativeBase.metadata.drop_all(engine)
