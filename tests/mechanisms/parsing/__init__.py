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
import jinja2


LINE_BREAK = '\n' + '-' * 60


class Parsed(object):
    def __init__(self):
        self.issues = []
        self.text = ''
        self.verbose = False

    def assert_success(self):
        # See: https://docs.pytest.org/en/latest/example/simple.html
        #      #writing-well-integrated-assertion-helpers
        __tracebackhide__ = True                                                                    # pylint: disable=unused-variable

        if len(self.issues) > 0:
            pytest.fail(u'did not expect parsing errors\n\n{0}\n\n{1}'
                        .format(self.text.strip(), u'\n'.join(self.issues)))
        else:
            if self.verbose:
                print LINE_BREAK
                print self.text.strip()

    def assert_failure(self):
        # See: https://docs.pytest.org/en/latest/example/simple.html
        #      #writing-well-integrated-assertion-helpers
        __tracebackhide__ = True                                                                    # pylint: disable=unused-variable

        if len(self.issues) > 0:
            if self.verbose:
                print LINE_BREAK
                print u'{0}\n\n{1}'.format(self.text.strip(), u'\n'.join(self.issues))
        else:
            pytest.fail(u'expected parsing errors but got none\n\n{0}'
                        .format(self.text.strip()))


class Parser(object):
    def __init__(self):
        self.verbose = False

    def parse_literal(self, text, context=None, **kwargs):
        text = render(text, context)
        parsed = self._parse_literal(text, **kwargs)
        parsed.verbose = self.verbose
        return parsed

    def _parse_literal(self, text, **kwargs):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def render(template, context=None):
    if not isinstance(template, unicode):
        template = template.decode('utf-8')
    template = jinja2.Template(template)
    template = template.render(context or {})
    return template
