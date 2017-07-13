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


from ...exceptions import AriaException
from ...utils.exceptions import print_exception
from ..validation import Issue


class Consumer(object):
    """
    Base class for ARIA consumers.

    Consumers provide useful functionality by consuming presentations.
    """

    def __init__(self, context):
        from ...orchestrator import topology

        self.topology = topology.Topology()
        self.context = context

    def consume(self):
        pass

    def dump(self):
        pass

    def _handle_exception(self, e):
        if hasattr(e, 'issue') and isinstance(e.issue, Issue):
            self.context.validation.report(issue=e.issue)
        else:
            self.context.validation.report(exception=e)
        if not isinstance(e, AriaException):
            print_exception(e)


class ConsumerChain(Consumer):
    """
    ARIA consumer chain.

    Calls consumers in order, handling exception by calling ``_handle_exception`` on them, and stops
    the chain if there are any validation issues.
    """

    def __init__(self, context, consumer_classes=None, handle_exceptions=True):
        super(ConsumerChain, self).__init__(context)
        self.handle_exceptions = handle_exceptions
        self.consumers = []
        if consumer_classes:
            for consumer_class in consumer_classes:
                self.append(consumer_class)

    def append(self, *consumer_classes):
        for consumer_class in consumer_classes:
            self.consumers.append(consumer_class(self.context))

    def consume(self):
        for consumer in self.consumers:
            try:
                consumer.consume()
            except BaseException as e:
                if self.handle_exceptions:
                    handle_exception(consumer, e)
                else:
                    raise e

            if consumer.topology.has_issues:
                self.context.validation.extend_issues(consumer.topology.issues)

            if self.context.validation.has_issues:
                break


def handle_exception(consumer, e):
    if isinstance(e, AriaException) and e.issue:
        consumer.context.validation.report(issue=e.issue)
    else:
        consumer.context.validation.report(exception=e)
    if not isinstance(e, AriaException):
        print_exception(e)
