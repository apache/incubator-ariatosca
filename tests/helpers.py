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

from . import ROOT_DIR
from .resources import DIR as RESOURCES_DIR


def get_example_uri(*args):
    return os.path.join(ROOT_DIR, 'examples', *args)


def get_resource_uri(*args):
    return os.path.join(RESOURCES_DIR, *args)


def get_service_template_uri(*args):
    return os.path.join(RESOURCES_DIR, 'service-templates', *args)
