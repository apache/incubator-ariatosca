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

from .. import VERSION
from ..consumption import ConsumptionContext
from ..loading import (UriLocation, URI_LOADER_PREFIXES)
from ..utils import (ArgumentParser, import_fullname, cachedmethod)

class BaseArgumentParser(ArgumentParser):
    def __init__(self, description, **kwargs):
        super(BaseArgumentParser, self).__init__(
            description='%s for ARIA version %s' % (description, VERSION), **kwargs)

class CommonArgumentParser(BaseArgumentParser):
    def __init__(self, description, **kwargs):
        super(CommonArgumentParser, self).__init__(description, **kwargs)

        self.add_argument('--loader-source',
                          default='aria.loading.DefaultLoaderSource',
                          help='loader source class for the parser')
        self.add_argument('--reader-source',
                          default='aria.reading.DefaultReaderSource',
                          help='reader source class for the parser')
        self.add_argument('--presenter-source',
                          default='aria.presentation.DefaultPresenterSource',
                          help='presenter source class for the parser')
        self.add_argument('--presenter', help='force use of this presenter class in parser')
        self.add_argument('--prefix', nargs='*', help='prefixes for imports')
        self.add_flag_argument('debug',
                               help_true='print debug info',
                               help_false='don\'t print debug info')
        self.add_flag_argument('cached-methods',
                               help_true='enable cached methods',
                               help_false='disable cached methods',
                               default=True)

    def parse_known_args(self, args=None, namespace=None):
        namespace, args = super(CommonArgumentParser, self).parse_known_args(args, namespace)

        if namespace.prefix:
            for prefix in namespace.prefix:
                URI_LOADER_PREFIXES.append(prefix)

        cachedmethod.ENABLED = namespace.cached_methods

        return namespace, args

def create_context_from_namespace(namespace, **kwargs):
    args = vars(namespace).copy()
    args.update(kwargs)
    return create_context(**args)

def create_context(uri, loader_source, reader_source, presenter_source, presenter, debug, **kwargs):
    context = ConsumptionContext()
    context.loading.loader_source = import_fullname(loader_source)()
    context.reading.reader_source = import_fullname(reader_source)()
    context.presentation.location = UriLocation(uri) if isinstance(uri, basestring) else uri
    context.presentation.presenter_source = import_fullname(presenter_source)()
    context.presentation.presenter_class = import_fullname(presenter)
    context.presentation.print_exceptions = debug
    return context
