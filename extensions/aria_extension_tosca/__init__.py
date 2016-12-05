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

from aria import extension

from .simple_v1_0 import ToscaSimplePresenter1_0
from .simple_nfv_v1_0 import ToscaSimpleNfvPresenter1_0


@extension.parser
class ParserExtensions(object):

    @staticmethod
    def presenter_class():
        return ToscaSimplePresenter1_0, ToscaSimpleNfvPresenter1_0

    @staticmethod
    def specification_package():
        return 'aria_extension_tosca'

    @staticmethod
    def specification_url():
        return {
            'yaml-1.1': 'http://yaml.org',
            'tosca-simple-1.0': 'http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/'
                                'cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html',
            'tosca-simple-nfv-1.0': 'http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/'
                                    'tosca-nfv-v1.0.html'
        }

    @staticmethod
    def uri_loader_prefix():
        the_dir = os.path.dirname(__file__)
        return os.path.join(the_dir, 'profiles')


MODULES = (
    'simple_v1_0',
    'simple_nfv_v1_0')

__all__ = (
    'MODULES',
    'install_aria_extension')
