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

import pytest
from sqlalchemy import Column, Text, Integer, event

from aria.modeling import (
    bases,
    exceptions,
    types as modeling_types,
    models
)
from aria.storage import (
    ModelStorage,
    sql_mapi,
    instrumentation
)

from ..storage import release_sqlite_storage, init_inmemory_model_storage

STUB = instrumentation._STUB
Value = instrumentation._Value
instruments_holder = []


class TestInstrumentation(object):

    def test_track_changes(self, storage):
        model_kwargs = dict(
            name='name',
            dict1={'initial': 'value'},
            dict2={'initial': 'value'},
            list1=['initial'],
            list2=['initial'],
            int1=0,
            int2=0,
            string2='string')
        model1_instance = MockModel1(**model_kwargs)
        model2_instance = MockModel2(**model_kwargs)
        storage.mock_model_1.put(model1_instance)
        storage.mock_model_2.put(model2_instance)

        instrument = self._track_changes({
            MockModel1.dict1: dict,
            MockModel1.list1: list,
            MockModel1.int1: int,
            MockModel1.string2: str,
            MockModel2.dict2: dict,
            MockModel2.list2: list,
            MockModel2.int2: int,
            MockModel2.name: str
        })

        assert not instrument.tracked_changes

        storage_model1_instance = storage.mock_model_1.get(model1_instance.id)
        storage_model2_instance = storage.mock_model_2.get(model2_instance.id)

        storage_model1_instance.dict1 = {'hello': 'world'}
        storage_model1_instance.dict2 = {'should': 'not track'}
        storage_model1_instance.list1 = ['hello']
        storage_model1_instance.list2 = ['should not track']
        storage_model1_instance.int1 = 100
        storage_model1_instance.int2 = 20000
        storage_model1_instance.name = 'should not track'
        storage_model1_instance.string2 = 'new_string'

        storage_model2_instance.dict1.update({'should': 'not track'})
        storage_model2_instance.dict2.update({'hello': 'world'})
        storage_model2_instance.list1.append('should not track')
        storage_model2_instance.list2.append('hello')
        storage_model2_instance.int1 = 100
        storage_model2_instance.int2 = 20000
        storage_model2_instance.name = 'new_name'
        storage_model2_instance.string2 = 'should not track'

        assert instrument.tracked_changes == {
            'mock_model_1': {
                model1_instance.id: {
                    'dict1': Value(STUB, {'hello': 'world'}),
                    'list1': Value(STUB, ['hello']),
                    'int1': Value(STUB, 100),
                    'string2': Value(STUB, 'new_string')
                }
            },
            'mock_model_2': {
                model2_instance.id: {
                    'dict2': Value({'initial': 'value'}, {'hello': 'world', 'initial': 'value'}),
                    'list2': Value(['initial'], ['initial', 'hello']),
                    'int2': Value(STUB, 20000),
                    'name': Value(STUB, 'new_name'),
                }
            }
        }

    def test_attribute_initial_none_value(self, storage):
        instance1 = MockModel1(name='name1', dict1=None)
        instance2 = MockModel1(name='name2', dict1=None)
        storage.mock_model_1.put(instance1)
        storage.mock_model_1.put(instance2)
        instrument = self._track_changes({MockModel1.dict1: dict})
        instance1 = storage.mock_model_1.get(instance1.id)
        instance2 = storage.mock_model_1.get(instance2.id)
        instance1.dict1 = {'new': 'value'}
        assert instrument.tracked_changes == {
            'mock_model_1': {
                instance1.id: {'dict1': Value(STUB, {'new': 'value'})},
                instance2.id: {'dict1': Value(None, None)},
            }
        }

    def test_attribute_set_none_value(self, storage):
        instance = MockModel1(name='name')
        storage.mock_model_1.put(instance)
        instrument = self._track_changes({
            MockModel1.dict1: dict,
            MockModel1.list1: list,
            MockModel1.string2: str,
            MockModel1.int1: int
        })
        instance = storage.mock_model_1.get(instance.id)
        instance.dict1 = None
        instance.list1 = None
        instance.string2 = None
        instance.int1 = None
        assert instrument.tracked_changes == {
            'mock_model_1': {
                instance.id: {
                    'dict1': Value(STUB, None),
                    'list1': Value(STUB, None),
                    'string2': Value(STUB, None),
                    'int1': Value(STUB, None)
                }
            }
        }

    def test_restore(self):
        instrument = self._track_changes({MockModel1.dict1: dict})
        # set instance attribute, load instance, refresh instance and flush_refresh listeners
        assert len(instrument.listeners) == 4
        for listener_args in instrument.listeners:
            assert event.contains(*listener_args)
        instrument.restore()
        assert len(instrument.listeners) == 4
        for listener_args in instrument.listeners:
            assert not event.contains(*listener_args)
        return instrument

    def test_restore_twice(self):
        instrument = self.test_restore()
        instrument.restore()

    def test_instrumentation_context_manager(self, storage):
        instance = MockModel1(name='name')
        storage.mock_model_1.put(instance)
        with self._track_changes({MockModel1.dict1: dict}) as instrument:
            instance = storage.mock_model_1.get(instance.id)
            instance.dict1 = {'new': 'value'}
            assert instrument.tracked_changes == {
                'mock_model_1': {instance.id: {'dict1': Value(STUB, {'new': 'value'})}}
            }
            assert len(instrument.listeners) == 4
            for listener_args in instrument.listeners:
                assert event.contains(*listener_args)
        for listener_args in instrument.listeners:
            assert not event.contains(*listener_args)

    def test_apply_tracked_changes(self, storage):
        initial_values = {'dict1': {'initial': 'value'}, 'list1': ['initial']}
        instance1_1 = MockModel1(name='instance1_1', **initial_values)
        instance1_2 = MockModel1(name='instance1_2', **initial_values)
        instance2_1 = MockModel2(name='instance2_1', **initial_values)
        instance2_2 = MockModel2(name='instance2_2', **initial_values)
        storage.mock_model_1.put(instance1_1)
        storage.mock_model_1.put(instance1_2)
        storage.mock_model_2.put(instance2_1)
        storage.mock_model_2.put(instance2_2)

        instrument = self._track_changes({
            MockModel1.dict1: dict,
            MockModel1.list1: list,
            MockModel2.dict1: dict,
            MockModel2.list1: list
        })

        def get_instances():
            return (storage.mock_model_1.get(instance1_1.id),
                    storage.mock_model_1.get(instance1_2.id),
                    storage.mock_model_2.get(instance2_1.id),
                    storage.mock_model_2.get(instance2_2.id))

        instance1_1, instance1_2, instance2_1, instance2_2 = get_instances()
        instance1_1.dict1 = {'new': 'value'}
        instance1_2.list1 = ['new_value']
        instance2_1.dict1.update({'new': 'value'})
        instance2_2.list1.append('new_value')

        instrument.restore()
        storage.mock_model_1._session.expire_all()

        instance1_1, instance1_2, instance2_1, instance2_2 = get_instances()
        instance1_1.dict1 = {'overriding': 'value'}
        instance1_2.list1 = ['overriding_value']
        instance2_1.dict1 = {'overriding': 'value'}
        instance2_2.list1 = ['overriding_value']
        storage.mock_model_1.put(instance1_1)
        storage.mock_model_1.put(instance1_2)
        storage.mock_model_2.put(instance2_1)
        storage.mock_model_2.put(instance2_2)
        instance1_1, instance1_2, instance2_1, instance2_2 = get_instances()
        assert instance1_1.dict1 == {'overriding': 'value'}
        assert instance1_2.list1 == ['overriding_value']
        assert instance2_1.dict1 == {'overriding': 'value'}
        assert instance2_2.list1 == ['overriding_value']

        instrumentation.apply_tracked_changes(
            tracked_changes=instrument.tracked_changes,
            model=storage)

        instance1_1, instance1_2, instance2_1, instance2_2 = get_instances()
        assert instance1_1.dict1 == {'new': 'value'}
        assert instance1_2.list1 == ['new_value']
        assert instance2_1.dict1 == {'initial': 'value', 'new': 'value'}
        assert instance2_2.list1 == ['initial', 'new_value']

    def test_clear_instance(self, storage):
        instance1 = MockModel1(name='name1')
        instance2 = MockModel1(name='name2')
        for instance in [instance1, instance2]:
            storage.mock_model_1.put(instance)
        instrument = self._track_changes({MockModel1.dict1: dict})
        instance1.dict1 = {'new': 'value'}
        instance2.dict1 = {'new2': 'value2'}
        assert instrument.tracked_changes == {
            'mock_model_1': {
                instance1.id: {'dict1': Value(STUB, {'new': 'value'})},
                instance2.id: {'dict1': Value(STUB, {'new2': 'value2'})}
            }
        }
        instrument.clear(instance1)
        assert instrument.tracked_changes == {
            'mock_model_1': {
                instance2.id: {'dict1': Value(STUB, {'new2': 'value2'})}
            }
        }

    def test_clear_all(self, storage):
        instance1 = MockModel1(name='name1')
        instance2 = MockModel1(name='name2')
        for instance in [instance1, instance2]:
            storage.mock_model_1.put(instance)
        instrument = self._track_changes({MockModel1.dict1: dict})
        instance1.dict1 = {'new': 'value'}
        instance2.dict1 = {'new2': 'value2'}
        assert instrument.tracked_changes == {
            'mock_model_1': {
                instance1.id: {'dict1': Value(STUB, {'new': 'value'})},
                instance2.id: {'dict1': Value(STUB, {'new2': 'value2'})}
            }
        }
        instrument.clear()
        assert instrument.tracked_changes == {}

    def _track_changes(self, instrumented):
        instrument = instrumentation.track_changes(instrumented)
        instruments_holder.append(instrument)
        return instrument

    def test_track_changes_to_strict_dict(self, storage):
        model_kwargs = dict(strict_dict={'key': 'value'},
                            strict_list=['item'])
        mode_instance = StrictMockModel(**model_kwargs)
        storage.strict_mock_model.put(mode_instance)

        instrument = self._track_changes({
            StrictMockModel.strict_dict: dict,
            StrictMockModel.strict_list: list,
        })

        assert not instrument.tracked_changes

        storage_model_instance = storage.strict_mock_model.get(mode_instance.id)

        with pytest.raises(exceptions.StorageError):
            storage_model_instance.strict_dict = {1: 1}

        with pytest.raises(exceptions.StorageError):
            storage_model_instance.strict_dict = {'hello': 1}

        with pytest.raises(exceptions.StorageError):
            storage_model_instance.strict_dict = {1: 'hello'}

        storage_model_instance.strict_dict = {'hello': 'world'}
        assert storage_model_instance.strict_dict == {'hello': 'world'}

        with pytest.raises(exceptions.StorageError):
            storage_model_instance.strict_list = [1]
        storage_model_instance.strict_list = ['hello']
        assert storage_model_instance.strict_list == ['hello']

        assert instrument.tracked_changes == {
            'strict_mock_model': {
                mode_instance.id: {
                    'strict_dict': Value(STUB, {'hello': 'world'}),
                    'strict_list': Value(STUB, ['hello']),
                }
            },
        }


@pytest.fixture(autouse=True)
def restore_instrumentation():
    yield
    for instrument in instruments_holder:
        instrument.restore()
    del instruments_holder[:]


@pytest.fixture
def storage():
    result = ModelStorage(api_cls=sql_mapi.SQLAlchemyModelAPI,
                          items=(MockModel1, MockModel2, StrictMockModel),
                          initiator=init_inmemory_model_storage)
    yield result
    release_sqlite_storage(result)


class _MockModel(bases.ModelMixin):
    name = Column(Text)
    dict1 = Column(modeling_types.Dict)
    dict2 = Column(modeling_types.Dict)
    list1 = Column(modeling_types.List)
    list2 = Column(modeling_types.List)
    int1 = Column(Integer)
    int2 = Column(Integer)
    string2 = Column(Text)


class MockModel1(_MockModel, models.aria_declarative_base):
    __tablename__ = 'mock_model_1'


class MockModel2(_MockModel, models.aria_declarative_base):
    __tablename__ = 'mock_model_2'


class StrictMockModel(bases.ModelMixin, models.aria_declarative_base):
    __tablename__ = 'strict_mock_model'

    strict_dict = Column(modeling_types.StrictDict(basestring, basestring))
    strict_list = Column(modeling_types.StrictList(basestring))
