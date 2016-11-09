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

from aria.storage.structures import (
    Field,
    IterField,
    PointerField,
    IterPointerField,
    Model,
)


def model_factory():
    class TestModel(Model):
        id = Field(default='test_id')
    return TestModel()


def test_base_field():
    field = Field()
    assert vars(field) == vars(Field(type=None, choices=(), default=Field.NO_DEFAULT))


def test_type_check():
    field = Field(type=int)
    assert vars(field) == vars(Field(type=int, choices=(), default=Field.NO_DEFAULT))
    with pytest.raises(TypeError):
        field.validate_instance('field', 'any_value', int)
    field.validate_instance('field', 1, int)


def test_field_choices():
    field = Field(choices=[1, 2])
    assert vars(field) == vars(Field(type=None, choices=[1, 2], default=Field.NO_DEFAULT))
    field.validate_in_choice('field', 1, field.choices)

    with pytest.raises(TypeError):
        field.validate_in_choice('field', 'value', field.choices)


def test_field_without_default():
    class Test(object):
        field = Field()
    test = Test()
    with pytest.raises(AttributeError, message="'Test' object has no attribute 'field'"):
        assert test.field


def test_field_default_func():
    def true_func():
        return True

    field = Field(default=true_func)
    assert vars(field) == vars(Field(type=None, choices=(), default=true_func))
    assert field.default


def test_field_default():
    field = Field(default='value')
    assert vars(field) == vars(Field(type=None, choices=(), default='value'))


def test_iterable_field():
    iter_field = IterField(type=int)
    assert vars(iter_field) == vars(Field(type=int, default=Field.NO_DEFAULT))
    iter_field.validate_value('iter_field', [1, 2])
    with pytest.raises(TypeError):
        iter_field.validate_value('iter_field', ['a', 1])


def test_pointer_field():
    test_model = model_factory()

    pointer_field = PointerField(type=Model)
    assert vars(pointer_field) == \
        vars(PointerField(type=Model, choices=(), default=Field.NO_DEFAULT))
    with pytest.raises(AssertionError):
        PointerField(type=list)
    pointer_field.validate_value('pointer_field', test_model, None)
    with pytest.raises(TypeError):
        pointer_field.validate_value('pointer_field', int, None)


def test_iterable_pointer_field():
    test_model = model_factory()
    iter_pointer_field = IterPointerField(type=Model)
    assert vars(iter_pointer_field) == \
        vars(IterPointerField(type=Model, default=Field.NO_DEFAULT))
    with pytest.raises(AssertionError):
        IterPointerField(type=list)

    iter_pointer_field.validate_value('iter_pointer_field', [test_model, test_model], None)
    with pytest.raises(TypeError):
        iter_pointer_field.validate_value('iter_pointer_field', [int, test_model], None)


def test_custom_field_validation():
    def validation_func(name, value, instance):
        assert name == 'id'
        assert value == 'value'
        assert isinstance(instance, TestModel)

    class TestModel(Model):
        id = Field(default='_', validation_func=validation_func)

    obj = TestModel()
    obj.id = 'value'

    with pytest.raises(AssertionError):
        obj.id = 'not_value'
