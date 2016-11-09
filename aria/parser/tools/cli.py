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

from aria.parser import install_aria_extensions
from aria.parser.utils import (print_exception, import_fullname)
from aria.parser.tools.utils import (CommonArgumentParser, create_context_from_namespace)
from aria.parser.consumption import (ConsumerChain, Read, Validate, Model, Types, Inputs, Instance)

class ArgumentParser(CommonArgumentParser):
    def __init__(self):
        super(ArgumentParser, self).__init__(description='CLI', prog='aria')
        self.add_argument('uri', help='URI or file path to profile')
        self.add_argument('consumer',
                          nargs='?',
                          default='instance',
                          help='consumer class name (full class path or short name)')

def main():
    try:

        args, unknown_args = ArgumentParser().parse_known_args()

        install_aria_extensions()

        context = create_context_from_namespace(args)
        context.args = unknown_args

        consumer = ConsumerChain(context, (Read, Validate))

        consumer_class_name = args.consumer
        dumper = None
        if consumer_class_name == 'presentation':
            dumper = consumer.consumers[0]
        elif consumer_class_name == 'model':
            consumer.append(Model)
        elif consumer_class_name == 'types':
            consumer.append(Model, Types)
        elif consumer_class_name == 'instance':
            consumer.append(Model, Inputs, Instance)
        else:
            consumer.append(Model, Inputs, Instance)
            consumer.append(import_fullname(consumer_class_name))

        if dumper is None:
            # Default to last consumer
            dumper = consumer.consumers[-1]

        consumer.consume()

        if not context.validation.dump_issues():
            dumper.dump()

    except Exception as e:
        print_exception(e)

if __name__ == '__main__':
    main()
