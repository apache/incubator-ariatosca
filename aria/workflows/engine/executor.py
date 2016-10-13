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

from aria.events import (
    start_task_signal,
    on_success_task_signal,
    on_failure_task_signal,
)


class Executor(object):

    def execute(self, task):
        raise NotImplementedError

    def task_started(self, task_id):
        start_task_signal.send(self, task_id=task_id)

    def task_failed(self, task_id, exception):
        on_failure_task_signal.send(self, task_id=task_id, exception=exception)

    def task_succeeded(self, task_id):
        on_success_task_signal.send(self, task_id=task_id)


class LocalExecutor(Executor):

    def execute(self, task):
        pass
