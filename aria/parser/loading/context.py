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


from ...utils.collections import StrictList
from .source import DefaultLoaderSource


class LoadingContext(object):
    """
    Properties:

    * :code:`loader_source`: For finding loader instances
    * :code:`prefixes`: List of additional prefixes for :class:`UriTextLoader`
    """

    def __init__(self):
        self.loader_source = DefaultLoaderSource()
        self.prefixes = StrictList(value_class=basestring)
