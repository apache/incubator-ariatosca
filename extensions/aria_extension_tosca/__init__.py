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

import os.path

from aria.parser import DSL_SPECIFICATION_PACKAGES
from aria.parser.presentation import PRESENTER_CLASSES
from aria.parser.loading import URI_LOADER_PREFIXES

from .simple_v1_0 import ToscaSimplePresenter1_0
from .simple_nfv_v1_0 import ToscaSimpleNfvPresenter1_0

def install_aria_extension():
    '''
    Installs the TOSCA extension to ARIA.
    '''

    global PRESENTER_CLASSES # pylint: disable=global-statement
    PRESENTER_CLASSES += (ToscaSimplePresenter1_0, ToscaSimpleNfvPresenter1_0)

    # DSL specification
    DSL_SPECIFICATION_PACKAGES.append('aria_extension_tosca')

    # Imports
    the_dir = os.path.dirname(__file__)
    URI_LOADER_PREFIXES.append(os.path.join(the_dir, 'profiles'))

MODULES = (
    'simple_v1_0',
    'simple_nfv_v1_0')

__all__ = (
    'MODULES',
    'install_aria_extension')
