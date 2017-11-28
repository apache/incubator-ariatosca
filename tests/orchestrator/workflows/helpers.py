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

from contextlib import contextmanager

from aria.orchestrator import events
from aria.orchestrator.workflows.core import events_handler


@contextmanager
def events_collector(*signals):
    handlers = {}
    collected = {}

    def handler_factory(key):
        def handler(*args, **kwargs):
            signal_events = collected.setdefault(key, [])
            signal_events.append({'args': args, 'kwargs': kwargs})
        handlers[signal] = handler
        return handler

    for signal in signals:
        signal.connect(handler_factory(signal))
    try:
        yield collected
    finally:
        for signal in signals:
            signal.disconnect(handlers[signal])


@contextmanager
def disconnect_event_handlers():
    # disconnect the system events handler
    events.start_task_signal.disconnect(events_handler._task_started)
    events.on_success_task_signal.disconnect(events_handler._task_succeeded)
    events.on_failure_task_signal.disconnect(events_handler._task_failed)
    try:
        yield
    finally:
        # reconnect the system events handler
        events.start_task_signal.connect(events_handler._task_started)
        events.on_success_task_signal.connect(events_handler._task_succeeded)
        events.on_failure_task_signal.connect(events_handler._task_failed)
