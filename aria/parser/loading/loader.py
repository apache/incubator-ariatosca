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


class Loader(object):
    """
    Base class for ARIA loaders.

    Loaders extract a document by consuming a document source.

    Though the extracted document is often textual (a string or string-like data), loaders may
    provide any format.

    Loaders can also calculate the "canonical location" of what they are loading, which is a
    globally unique reference that can be used as a cache key. Examples include absolute file paths
    and de-relativized URIs. Note that calculating the canonical location can be very costly
    (for example, hitting various URLs until finding an existing one), and thus it's a good idea
    to cache the canonical location per loader context.
    """

    def open(self):
        pass

    def close(self):
        pass

    def load(self):
        raise NotImplementedError

    def get_canonical_location(self):
        raise NotImplementedError
