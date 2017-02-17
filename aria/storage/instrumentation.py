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

import copy

import sqlalchemy.event

from ..modeling import model as _model

_STUB = object()
_INSTRUMENTED = {
    _model.Node.runtime_properties: dict
}


def track_changes(instrumented=None):
    """Track changes in the specified model columns

    This call will register event listeners using sqlalchemy's event mechanism. The listeners
    instrument all returned objects such that the attributes specified in ``instrumented``, will
    be replaced with a value that is stored in the returned instrumentation context
    ``tracked_changes`` property.

    Why should this be implemented when sqlalchemy already does a fantastic job at tracking changes
    you ask? Well, when sqlalchemy is used with sqlite, due to how sqlite works, only one process
    can hold a write lock to the database. This does not work well when ARIA runs tasks in
    subprocesses (by the process executor) and these tasks wish to change some state as well. These
    tasks certainly deserve a chance to do so!

    To enable this, the subprocess calls ``track_changes()`` before any state changes are made.
    At the end of the subprocess execution, it should return the ``tracked_changes`` attribute of
    the instrumentation context returned from this call, to the parent process. The parent process
    will then call ``apply_tracked_changes()`` that resides in this module as well.
    At that point, the changes will actually be written back to the database.

    :param instrumented: A dict from model columns to their python native type
    :return: The instrumentation context
    """
    return _Instrumentation(instrumented or _INSTRUMENTED)


class _Instrumentation(object):

    def __init__(self, instrumented):
        self.tracked_changes = {}
        self.listeners = []
        self._track_changes(instrumented)

    def _track_changes(self, instrumented):
        instrumented_classes = {}
        for instrumented_attribute, attribute_type in instrumented.items():
            self._register_set_attribute_listener(
                instrumented_attribute=instrumented_attribute,
                attribute_type=attribute_type)
            instrumented_class = instrumented_attribute.parent.entity
            instrumented_class_attributes = instrumented_classes.setdefault(instrumented_class, {})
            instrumented_class_attributes[instrumented_attribute.key] = attribute_type
        for instrumented_class, instrumented_attributes in instrumented_classes.items():
            self._register_instance_listeners(
                instrumented_class=instrumented_class,
                instrumented_attributes=instrumented_attributes)

    def _register_set_attribute_listener(self, instrumented_attribute, attribute_type):
        def listener(target, value, *_):
            mapi_name = target.__modelname__
            tracked_instances = self.tracked_changes.setdefault(mapi_name, {})
            tracked_attributes = tracked_instances.setdefault(target.id, {})
            if value is None:
                current = None
            else:
                current = copy.deepcopy(attribute_type(value))
            tracked_attributes[instrumented_attribute.key] = _Value(_STUB, current)
            return current
        listener_args = (instrumented_attribute, 'set', listener)
        sqlalchemy.event.listen(*listener_args, retval=True)
        self.listeners.append(listener_args)

    def _register_instance_listeners(self, instrumented_class, instrumented_attributes):
        def listener(target, *_):
            mapi_name = instrumented_class.__modelname__
            tracked_instances = self.tracked_changes.setdefault(mapi_name, {})
            tracked_attributes = tracked_instances.setdefault(target.id, {})
            for attribute_name, attribute_type in instrumented_attributes.items():
                if attribute_name not in tracked_attributes:
                    initial = getattr(target, attribute_name)
                    if initial is None:
                        current = None
                    else:
                        current = copy.deepcopy(attribute_type(initial))
                    tracked_attributes[attribute_name] = _Value(initial, current)
                target.__dict__[attribute_name] = tracked_attributes[attribute_name].current
        for listener_args in [(instrumented_class, 'load', listener),
                              (instrumented_class, 'refresh', listener),
                              (instrumented_class, 'refresh_flush', listener)]:
            sqlalchemy.event.listen(*listener_args)
            self.listeners.append(listener_args)

    def clear(self, target=None):
        if target:
            mapi_name = target.__modelname__
            tracked_instances = self.tracked_changes.setdefault(mapi_name, {})
            tracked_instances.pop(target.id, None)
        else:
            self.tracked_changes.clear()

    def restore(self):
        """Remove all listeners registered by this instrumentation"""
        for listener_args in self.listeners:
            if sqlalchemy.event.contains(*listener_args):
                sqlalchemy.event.remove(*listener_args)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()


class _Value(object):
    # You may wonder why is this a full blown class and not a named tuple. The reason is that
    # jsonpickle that is used to serialize the tracked_changes, does not handle named tuples very
    # well. At the very least, I could not get it to behave.

    def __init__(self, initial, current):
        self.initial = initial
        self.current = current

    def __eq__(self, other):
        if not isinstance(other, _Value):
            return False
        return self.initial == other.initial and self.current == other.current

    def __hash__(self):
        return hash(self.initial) ^ hash(self.current)


def apply_tracked_changes(tracked_changes, model):
    """Write tracked changes back to the database using provided model storage

    :param tracked_changes: The ``tracked_changes`` attribute of the instrumentation context
                            returned by calling ``track_changes()``
    :param model: The model storage used to actually apply the changes
    """
    for mapi_name, tracked_instances in tracked_changes.items():
        mapi = getattr(model, mapi_name)
        for instance_id, tracked_attributes in tracked_instances.items():
            instance = None
            for attribute_name, value in tracked_attributes.items():
                if value.initial != value.current:
                    if not instance:
                        instance = mapi.get(instance_id)
                    setattr(instance, attribute_name, value.current)
            if instance:
                mapi.update(instance)
