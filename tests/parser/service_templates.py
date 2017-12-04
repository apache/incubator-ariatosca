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

from aria.utils.caching import cachedmethod
from aria.parser.loading import LiteralLocation

from .utils import (create_context, create_consumer)
from ..helpers import (get_example_uri, get_service_template_uri)


def consume_literal(literal, consumer_class_name='instance', cache=True, no_issues=True):
    cachedmethod.ENABLED = cache
    context = create_context(LiteralLocation(literal))
    consumer, dumper = create_consumer(context, consumer_class_name)
    consumer.consume()
    if no_issues:
        context.validation.dump_issues()
        assert not context.validation.has_issues
    return context, dumper


def consume_use_case(use_case_name, consumer_class_name='instance', cache=True):
    cachedmethod.ENABLED = cache
    uri = get_example_uri('tosca-simple-1.0', 'use-cases', use_case_name,
                          '{0}.yaml'.format(use_case_name))
    context = create_context(uri)
    inputs_file = get_example_uri('tosca-simple-1.0', 'use-cases', use_case_name, 'inputs.yaml')
    if os.path.isfile(inputs_file):
        context.args.append('--inputs={0}'.format(inputs_file))
    consumer, dumper = create_consumer(context, consumer_class_name)
    consumer.consume()
    context.validation.dump_issues()
    assert not context.validation.has_issues
    return context, dumper


def consume_types_use_case(use_case_name, consumer_class_name='instance', cache=True):
    cachedmethod.ENABLED = cache
    uri = get_service_template_uri('tosca-simple-1.0', 'types', use_case_name,
                                   '{0}.yaml'.format(use_case_name))
    context = create_context(uri)
    inputs_file = get_example_uri('tosca-simple-1.0', 'types', use_case_name, 'inputs.yaml')
    if os.path.isfile(inputs_file):
        context.args.append('--inputs={0}'.format(inputs_file))
    consumer, dumper = create_consumer(context, consumer_class_name)
    consumer.consume()
    context.validation.dump_issues()
    assert not context.validation.has_issues
    return context, dumper

def consume_import_use_case(use_case_name, consumer_class_name='instance',
                            plugin_dir=None, cache=True):
    cachedmethod.ENABLED = cache
    uri = get_service_template_uri('tosca-simple-1.0', 'imports', use_case_name,
                                   '{0}.yaml'.format(use_case_name))
    context = create_context(uri, plugin_dir=plugin_dir)
    inputs_file = get_example_uri('tosca-simple-1.0', 'imports', use_case_name, 'inputs.yaml')
    if os.path.isfile(inputs_file):
        context.args.append('--inputs={0}'.format(inputs_file))
    consumer, dumper = create_consumer(context, consumer_class_name)
    consumer.consume()
    context.validation.dump_issues()
    assert not context.validation.has_issues
    return context, dumper


def consume_node_cellar(consumer_class_name='instance', cache=True):
    consume_test_case(
        get_service_template_uri('tosca-simple-1.0', 'node-cellar', 'node-cellar.yaml'),
        consumer_class_name=consumer_class_name,
        inputs_uri=get_service_template_uri('tosca-simple-1.0', 'node-cellar', 'inputs.yaml'),
        cache=cache

    )


def consume_test_case(uri, inputs_uri=None, consumer_class_name='instance', cache=True):
    cachedmethod.ENABLED = cache
    uri = get_service_template_uri(uri)
    context = create_context(uri)
    if inputs_uri:
        context.args.append('--inputs=' + get_service_template_uri(inputs_uri))
    consumer, dumper = create_consumer(context, consumer_class_name)
    consumer.consume()
    context.validation.dump_issues()
    assert not context.validation.has_issues
    return context, dumper
