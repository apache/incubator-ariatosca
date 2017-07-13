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

from . import issue


class ValidationContext(issue.ReporterMixin):
    """
    Validation context.

    :ivar allow_unknown_fields: when ``False`` (the default) will report an issue if an unknown
     field is used
    :vartype allow_unknown_fields: bool
    :ivar allow_primitive_coersion`: when ``False`` (the default) will not attempt to coerce
     primitive field types
    :vartype allow_primitive_coersion: bool
    :ivar max_level: maximum validation level to report (default is all)
    :vartype max_level: int
    """

    def __init__(self, *args, **kwargs):
        super(ValidationContext, self).__init__(*args, **kwargs)
        self.allow_unknown_fields = False
        self.allow_primitive_coersion = False
