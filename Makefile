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

EXTENSIONS=extensions
DOCS=docs
HTML=docs/html

.PHONY: clean aria-requirements docs-requirements docs
.DEFAULT_GOAL = test

clean:
	rm -rf "$(HTML)" .tox .coverage*
	-find . -type f -name '.coverage' -delete
	-find . -type d -name '.coverage' -exec rm -rf {} \; 2>/dev/null
	-find . -type d -name '*.egg-info' -exec rm -rf {} \; 2>/dev/null

install:
	pip install --upgrade .

requirements:
	pip install --upgrade --requirement requirements.txt

docs-requirements:
	pip install --upgrade --requirement "$(DOCS)/requirements.txt"

test-requirements:
	pip install tox==2.5.0

docs: docs-requirements requirements
	rm -rf "$(HTML)"
	sphinx-build -b html "$(DOCS)" "$(HTML)"

test: test-requirements requirements
	PYTHONPATH="$(EXTENSIONS):$(PYTHONPATH)" tox
