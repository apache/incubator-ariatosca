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

from aria import storage, modeling
from aria import application_model_storage


def test_models_prefix(mocker):
    prefix = 'tosca_'
    models_to_register = modeling.models.models_to_register
    try:
        mocker.patch.object(storage, 'ModelStorage')
        application_model_storage(None, models_prefix=prefix)
        assert all(model.__table__.name.startswith(prefix) for model in models_to_register)
    finally:
        for model in models_to_register:
            model.__table__.name = model.__table__.name.replace(prefix, '')
