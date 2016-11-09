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

from ..validation import Issue
from ..utils import merge, safe_repr
from .presentation import Presentation


class Presenter(Presentation):
    """
    Base class for ARIA presenters.

    Presenters provide a robust API over agnostic raw data.
    """

    DSL_VERSIONS = None
    ALLOWED_IMPORTED_DSL_VERSIONS = None

    @classmethod
    def can_present(cls, raw):
        dsl = raw.get('tosca_definitions_version')
        assert cls.DSL_VERSIONS
        return dsl in cls.DSL_VERSIONS

    def _validate_import(self, context, presentation):
        tosca_definitions_version = presentation.service_template.tosca_definitions_version
        assert self.ALLOWED_IMPORTED_DSL_VERSIONS
        if tosca_definitions_version is not None \
                and tosca_definitions_version not in self.__class__.ALLOWED_IMPORTED_DSL_VERSIONS:
            context.validation.report(
                'import "tosca_definitions_version" is not one of %s: %s'
                % (' or '.join([safe_repr(v)
                                for v in self.__class__.ALLOWED_IMPORTED_DSL_VERSIONS]),
                   presentation.service_template.tosca_definitions_version),
                locator=presentation._get_child_locator('inputs'),
                level=Issue.BETWEEN_TYPES)
            return False
        return True

    def _merge_import(self, presentation):
        merge(self._raw, presentation._raw)
        if hasattr(self._raw, '_locator') and hasattr(presentation._raw, '_locator'):
            self._raw._locator.merge(presentation._raw._locator)

    def _link_locators(self):
        if hasattr(self._raw, '_locator'):
            locator = self._raw._locator
            delattr(self._raw, '_locator')
            locator.link(self._raw)

    @staticmethod
    def _get_import_locations(context):
        raise NotImplementedError

    @staticmethod
    def _get_deployment_template(context):
        raise NotImplementedError
