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

from aria.modeling import models
from aria.storage import collection_instrumentation
from aria.orchestrator.context import operation

from tests import (
    mock,
    storage
)


class MockActor(object):
    def __init__(self):
        self.dict_ = {}
        self.list_ = []


class MockMAPI(object):

    def __init__(self):
        pass

    def put(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass


class CollectionInstrumentation(object):

    @pytest.fixture
    def actor(self):
        return MockActor()

    @pytest.fixture
    def model(self):
        return MockMAPI()

    @pytest.fixture
    def dict_(self, actor, model):
        return collection_instrumentation._InstrumentedDict(model, actor, 'dict_', models.Attribute)

    @pytest.fixture
    def list_(self, actor, model):
        return collection_instrumentation._InstrumentedList(model, actor, 'list_', models.Attribute)


class TestDict(CollectionInstrumentation):

    def test_keys(self, actor, dict_):
        dict_.update(
            {
                'key1': models.Attribute.wrap('key1', 'value1'),
                'key2': models.Attribute.wrap('key2', 'value2')
            }
        )
        assert sorted(dict_.keys()) == sorted(['key1', 'key2']) == sorted(actor.dict_.keys())

    def test_values(self, actor, dict_):
        dict_.update({
            'key1': models.Attribute.wrap('key1', 'value1'),
            'key2': models.Attribute.wrap('key1', 'value2')
        })
        assert (sorted(dict_.values()) ==
                sorted(['value1', 'value2']) ==
                sorted(v.value for v in actor.dict_.values()))

    def test_items(self, dict_):
        dict_.update({
            'key1': models.Attribute.wrap('key1', 'value1'),
            'key2': models.Attribute.wrap('key1', 'value2')
        })
        assert sorted(dict_.items()) == sorted([('key1', 'value1'), ('key2', 'value2')])

    def test_iter(self, actor, dict_):
        dict_.update({
            'key1': models.Attribute.wrap('key1', 'value1'),
            'key2': models.Attribute.wrap('key1', 'value2')
        })
        assert sorted(list(dict_)) == sorted(['key1', 'key2']) == sorted(actor.dict_.keys())

    def test_bool(self, dict_):
        assert not dict_
        dict_.update({
            'key1': models.Attribute.wrap('key1', 'value1'),
            'key2': models.Attribute.wrap('key1', 'value2')
        })
        assert dict_

    def test_set_item(self, actor, dict_):
        dict_['key1'] = models.Attribute.wrap('key1', 'value1')
        assert dict_['key1'] == 'value1' == actor.dict_['key1'].value
        assert isinstance(actor.dict_['key1'], models.Attribute)

    def test_nested(self, actor, dict_):
        dict_['key'] = {}
        assert isinstance(actor.dict_['key'], models.Attribute)
        assert dict_['key'] == actor.dict_['key'].value == {}

        dict_['key']['inner_key'] = 'value'

        assert len(dict_) == 1
        assert 'inner_key' in dict_['key']
        assert dict_['key']['inner_key'] == 'value'
        assert dict_['key'].keys() == ['inner_key']
        assert dict_['key'].values() == ['value']
        assert dict_['key'].items() == [('inner_key', 'value')]
        assert isinstance(actor.dict_['key'], models.Attribute)
        assert isinstance(dict_['key'], collection_instrumentation._InstrumentedDict)

        dict_['key'].update({'updated_key': 'updated_value'})
        assert len(dict_) == 1
        assert 'updated_key' in dict_['key']
        assert dict_['key']['updated_key'] == 'updated_value'
        assert sorted(dict_['key'].keys()) == sorted(['inner_key', 'updated_key'])
        assert sorted(dict_['key'].values()) == sorted(['value', 'updated_value'])
        assert sorted(dict_['key'].items()) == sorted([('inner_key', 'value'),
                                                       ('updated_key', 'updated_value')])
        assert isinstance(actor.dict_['key'], models.Attribute)
        assert isinstance(dict_['key'], collection_instrumentation._InstrumentedDict)

        dict_.update({'key': 'override_value'})
        assert len(dict_) == 1
        assert 'key' in dict_
        assert dict_['key'] == 'override_value'
        assert len(actor.dict_) == 1
        assert isinstance(actor.dict_['key'], models.Attribute)
        assert actor.dict_['key'].value == 'override_value'

    def test_get_item(self, actor, dict_):
        dict_['key1'] = models.Attribute.wrap('key1', 'value1')
        assert isinstance(actor.dict_['key1'], models.Attribute)

    def test_update(self, actor, dict_):
        dict_['key1'] = 'value1'

        new_dict = {'key2': 'value2'}
        dict_.update(new_dict)
        assert len(dict_) == 2
        assert dict_['key2'] == 'value2'
        assert isinstance(actor.dict_['key2'], models.Attribute)

        new_dict = {}
        new_dict.update(dict_)
        assert new_dict['key1'] == dict_['key1']

    def test_copy(self, dict_):
        dict_['key1'] = 'value1'

        new_dict = dict_.copy()
        assert new_dict is not dict_
        assert new_dict == dict_

        dict_['key1'] = 'value2'
        assert new_dict['key1'] == 'value1'
        assert dict_['key1'] == 'value2'

    def test_clear(self, dict_):
        dict_['key1'] = 'value1'
        dict_.clear()

        assert len(dict_) == 0


class TestList(CollectionInstrumentation):

    def test_append(self, actor, list_):
        list_.append(models.Attribute.wrap('name', 'value1'))
        list_.append('value2')
        assert len(actor.list_) == 2
        assert len(list_) == 2
        assert isinstance(actor.list_[0], models.Attribute)
        assert list_[0] == 'value1'

        assert isinstance(actor.list_[1], models.Attribute)
        assert list_[1] == 'value2'

        list_[0] = 'new_value1'
        list_[1] = 'new_value2'
        assert isinstance(actor.list_[1], models.Attribute)
        assert isinstance(actor.list_[1], models.Attribute)
        assert list_[0] == 'new_value1'
        assert list_[1] == 'new_value2'

    def test_iter(self, list_):
        list_.append('value1')
        list_.append('value2')
        assert sorted(list_) == sorted(['value1', 'value2'])

    def test_insert(self, actor, list_):
        list_.append('value1')
        list_.insert(0, 'value2')
        list_.insert(2, 'value3')
        list_.insert(10, 'value4')
        assert sorted(list_) == sorted(['value1', 'value2', 'value3', 'value4'])
        assert len(actor.list_) == 4

    def test_set(self, list_):
        list_.append('value1')
        list_.append('value2')

        list_[1] = 'value3'
        assert len(list_) == 2
        assert sorted(list_) == sorted(['value1', 'value3'])

    def test_insert_into_nested(self, actor, list_):
        list_.append([])

        list_[0].append('inner_item')
        assert isinstance(actor.list_[0], models.Attribute)
        assert len(list_) == 1
        assert list_[0][0] == 'inner_item'

        list_[0].append('new_item')
        assert isinstance(actor.list_[0], models.Attribute)
        assert len(list_) == 1
        assert list_[0][1] == 'new_item'

        assert list_[0] == ['inner_item', 'new_item']
        assert ['inner_item', 'new_item'] == list_[0]


class TestDictList(CollectionInstrumentation):
    def test_dict_in_list(self, actor, list_):
        list_.append({})
        assert len(list_) == 1
        assert isinstance(actor.list_[0], models.Attribute)
        assert actor.list_[0].value == {}

        list_[0]['key'] = 'value'
        assert list_[0]['key'] == 'value'
        assert len(actor.list_) == 1
        assert isinstance(actor.list_[0], models.Attribute)
        assert actor.list_[0].value['key'] == 'value'

    def test_list_in_dict(self, actor, dict_):
        dict_['key'] = []
        assert len(dict_) == 1
        assert isinstance(actor.dict_['key'], models.Attribute)
        assert actor.dict_['key'].value == []

        dict_['key'].append('value')
        assert dict_['key'][0] == 'value'
        assert len(actor.dict_) == 1
        assert isinstance(actor.dict_['key'], models.Attribute)
        assert actor.dict_['key'].value[0] == 'value'


class TestModelInstrumentation(object):

    @pytest.fixture
    def workflow_ctx(self, tmpdir):
        context = mock.context.simple(str(tmpdir), inmemory=True)
        yield context
        storage.release_sqlite_storage(context.model)

    def test_attributes_access(self, workflow_ctx):
        node = workflow_ctx.model.node.list()[0]
        task = models.Task(node=node)
        workflow_ctx.model.task.put(task)

        ctx = operation.NodeOperationContext(
            task.id, node.id, name='', service_id=workflow_ctx.model.service.list()[0].id,
            model_storage=workflow_ctx.model, resource_storage=workflow_ctx.resource,
            execution_id=1)

        def _run_assertions(is_under_ctx):
            def ctx_assert(expr):
                if is_under_ctx:
                    assert expr
                else:
                    assert not expr

            ctx_assert(isinstance(ctx.node.attributes,
                                  collection_instrumentation._InstrumentedDict))
            assert not isinstance(ctx.node.properties,
                                  collection_instrumentation._InstrumentedCollection)

            for rel in ctx.node.inbound_relationships:
                ctx_assert(isinstance(rel, collection_instrumentation._WrappedModel))
                ctx_assert(isinstance(rel.source_node.attributes,
                                      collection_instrumentation._InstrumentedDict))
                ctx_assert(isinstance(rel.target_node.attributes,
                                      collection_instrumentation._InstrumentedDict))

            for node in ctx.model.node:
                ctx_assert(isinstance(node.attributes,
                                      collection_instrumentation._InstrumentedDict))
                assert not isinstance(node.properties,
                                      collection_instrumentation._InstrumentedCollection)

            for rel in ctx.model.relationship:
                ctx_assert(isinstance(rel, collection_instrumentation._WrappedModel))

                ctx_assert(isinstance(rel.source_node.attributes,
                                      collection_instrumentation._InstrumentedDict))
                ctx_assert(isinstance(rel.target_node.attributes,
                                      collection_instrumentation._InstrumentedDict))

                assert not isinstance(rel.source_node.properties,
                                      collection_instrumentation._InstrumentedCollection)
                assert not isinstance(rel.target_node.properties,
                                      collection_instrumentation._InstrumentedCollection)

        with ctx.model.instrument(models.Node.attributes):
            _run_assertions(True)

        _run_assertions(False)
