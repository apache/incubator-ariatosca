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

from aria.utils.collections import FrozenList
from aria.utils.caching import cachedmethod

from ..simple_v1_0 import ToscaSimplePresenter1_0


class ToscaSimpleNfvPresenter1_0(ToscaSimplePresenter1_0): # pylint: disable=invalid-name,abstract-method
    """
    ARIA presenter for the `TOSCA Simple Profile for NFV v1.0 csd03 <http://docs.oasis-open.org
    /tosca/tosca-nfv/v1.0/csd03/tosca-nfv-v1.0-csd03.html>`__.

    Supported :code:`tosca_definitions_version` values:

    * :code:`tosca_simple_profile_for_nfv_1_0`
    """

    DSL_VERSIONS = ('tosca_simple_profile_for_nfv_1_0',)
    ALLOWED_IMPORTED_DSL_VERSIONS = ('tosca_simple_yaml_1_0', 'tosca_simple_profile_for_nfv_1_0')
    SIMPLE_PROFILE_FOR_NFV_LOCATION = 'tosca-simple-nfv-1.0/tosca-simple-nfv-1.0.yaml'

    # Presenter

    @cachedmethod
    def _get_import_locations(self, context):
        import_locations = super(ToscaSimpleNfvPresenter1_0, self)._get_import_locations(context)
        if context.presentation.import_profile:
            return FrozenList([self.SIMPLE_PROFILE_FOR_NFV_LOCATION] + import_locations)
        return import_locations
