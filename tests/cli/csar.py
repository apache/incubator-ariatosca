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

from aria.cli import csar
from ..helpers import get_resource_uri


def _create_archive(tmpdir, mocker):
    service_template_dir = get_resource_uri(os.path.join(
        'service-templates', 'tosca-simple-1.0', 'node-cellar', 'node-cellar.yaml'))
    csar_path = str(tmpdir.join('csar_archive.csar'))
    csar.write(service_template_dir, csar_path, mocker.MagicMock())
    return csar_path


def test_create_csar(tmpdir, mocker):
    csar_path = _create_archive(tmpdir, mocker)
    assert os.path.exists(csar_path)


def test_read_csar(tmpdir, mocker):
    csar_path = _create_archive(tmpdir, mocker)
    csar_reader = csar.read(csar_path)
    assert csar_reader
