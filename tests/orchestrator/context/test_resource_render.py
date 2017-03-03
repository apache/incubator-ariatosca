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

from tests import mock, storage

_IMPLICIT_CTX_TEMPLATE = '{{ctx.service_instance.name}}'
_IMPLICIT_CTX_TEMPLATE_PATH = 'implicit-ctx.template'
_VARIABLES_TEMPLATE = '{{variable}}'
_VARIABLES_TEMPLATE_PATH = 'variables.template'


def test_get_resource_and_render_implicit_ctx_no_variables(ctx):
    content = ctx.get_resource_and_render(_IMPLICIT_CTX_TEMPLATE_PATH)
    assert content == mock.models.SERVICE_NAME


def test_get_resource_and_render_provided_variables(ctx):
    variable = 'VARIABLE'
    content = ctx.get_resource_and_render(_VARIABLES_TEMPLATE_PATH,
                                          variables={'variable': variable})
    assert content == variable


def test_download_resource_and_render_implicit_ctx_no_variables(tmpdir, ctx):
    destination = tmpdir.join('destination')
    ctx.download_resource_and_render(destination=str(destination),
                                     path=_IMPLICIT_CTX_TEMPLATE_PATH)
    assert destination.read() == mock.models.SERVICE_NAME


def test_download_resource_and_render_provided_variables(tmpdir, ctx):
    destination = tmpdir.join('destination')
    variable = 'VARIABLE'
    ctx.download_resource_and_render(destination=str(destination),
                                     path=_VARIABLES_TEMPLATE_PATH,
                                     variables={'variable': variable})
    assert destination.read() == variable


@pytest.fixture
def ctx(tmpdir):
    context = mock.context.simple(str(tmpdir))
    yield context
    storage.release_sqlite_storage(context.model)


@pytest.fixture(autouse=True)
def resources(tmpdir, ctx):
    implicit_ctx_template_path = tmpdir.join(_IMPLICIT_CTX_TEMPLATE_PATH)
    implicit_ctx_template_path.write(_IMPLICIT_CTX_TEMPLATE)
    variables_template_path = tmpdir.join(_VARIABLES_TEMPLATE_PATH)
    variables_template_path.write(_VARIABLES_TEMPLATE)
    ctx.resource.deployment.upload(entry_id='1',
                                   source=str(implicit_ctx_template_path),
                                   path=_IMPLICIT_CTX_TEMPLATE_PATH)
    ctx.resource.deployment.upload(entry_id='1',
                                   source=str(variables_template_path),
                                   path=_VARIABLES_TEMPLATE_PATH)
