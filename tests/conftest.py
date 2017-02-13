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

import logging

import pytest

import aria


@pytest.fixture(scope='session', autouse=True)
def install_aria_extensions():
    aria.install_aria_extensions()


@pytest.fixture(autouse=True)
def logging_handler_cleanup(request):
    """
    Each time a test runs, the loggers do not clear. we need to manually clear them or we'd have
    logging overload.

    Since every type of logger (node/relationship/workflow) share the same name, we should
    clear the logger each test. This should not happen in real world use.
    :param request:
    :return:
    """
    def clear_logging_handlers():
        logged_ctx_names = [
            aria.orchestrator.context.workflow.WorkflowContext.__name__,
            aria.orchestrator.context.operation.NodeOperationContext.__name__,
            aria.orchestrator.context.operation.RelationshipOperationContext.__name__
        ]
        for logger_name in logged_ctx_names:
            logging.getLogger(logger_name).handlers = []
    request.addfinalizer(clear_logging_handlers)
