# -*- coding: utf-8 -*-
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

from aria.utils.versions import (VersionString, parse_version_string)


def test_version_string():
    # No qualifiers
    assert VersionString('20') == VersionString('20')
    assert VersionString('20') == VersionString('20.0')
    assert VersionString('20') == VersionString('20.0.0')
    assert VersionString('20') < VersionString('20.0.1')

    # With numeric qualifiers
    assert VersionString('20.0.1-1') < VersionString('20.0.1-2')
    assert VersionString('20.0.1-0') < VersionString('20.0.1')
    assert VersionString('20.0.1-1') < VersionString('20.0.1')

    # With prefixed qualifiers
    assert VersionString('20.0.1-beta1') < VersionString('20.0.1-beta2')
    assert VersionString('20.0.1-beta1') < VersionString('20.0.1-1')
    assert VersionString('20.0.1-beta1') < VersionString('20.0.1')
    assert VersionString('20.0.1-beta2') < VersionString('20.0.1-rc2')
    assert VersionString('20.0.1-alpha2') < VersionString('20.0.1-beta1')
    assert VersionString('20.0.1-dev2') < VersionString('20.0.1-ALPHA1')
    assert VersionString('20.0.1-DEV2') < VersionString('20.0.1-alpha1')

    # With Unicode qualifier
    assert VersionString(u'20.0.1-詠嘆調1') == VersionString(u'20.0.1-詠嘆調2')

    # Coercive comparisons
    assert VersionString('20.0.0') == VersionString(10 * 2)
    assert VersionString('20.0.0') == VersionString(20.0)

    # Non-VersionString comparisons
    assert VersionString('20.0.0') == 20
    assert VersionString('20.0.0') < '20.0.1'

    # Nulls
    assert VersionString() == VersionString()
    assert VersionString() == VersionString.NULL
    assert VersionString(None) == VersionString.NULL
    assert VersionString.NULL == None                                                               # pylint: disable=singleton-comparison
    assert VersionString.NULL == 0

    # Invalid version strings
    assert VersionString('maxim is maxim') == VersionString.NULL
    assert VersionString('20.maxim.0') == VersionString.NULL
    assert VersionString('20.0.0-maxim1') == VersionString.NULL
    assert VersionString('20.0.1-1.1') == VersionString.NULL

    # Sorts
    v1 = VersionString('20.0.0')
    v2 = VersionString('20.0.1-beta1')
    v3 = VersionString('20.0.1')
    v4 = VersionString('20.0.2')
    assert [v1, v2, v3, v4] == sorted([v4, v3, v2, v1], key=lambda v: v.key)

    # Sets
    v1 = VersionString('20.0.0')
    v2 = VersionString('20.0')
    v3 = VersionString('20')
    assert set([v1]) == set([v1, v2, v3])

    # Dicts
    the_dict = {v1: 'test'}
    assert the_dict.get(v2) == 'test'

def test_parse_version_string():
    # One test of each type from the groups above should be enough
    assert parse_version_string('20') < parse_version_string('20.0.1')
    assert parse_version_string('20.0.1-1') < parse_version_string('20.0.1-2')
    assert parse_version_string('20.0.1-beta1') < parse_version_string('20.0.1-beta2')
    assert parse_version_string('20.0.0') == parse_version_string(10 * 2)
    assert parse_version_string(None) == parse_version_string(0)
    assert parse_version_string(None) == parse_version_string('maxim is maxim')
