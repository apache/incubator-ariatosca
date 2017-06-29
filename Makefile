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

EXTENSIONS = ./extensions
DIST = ./dist
DOCS = ./docs
HTML = ./docs/html
EASY_INSTALL_PTH = $(VIRTUAL_ENV)/lib/python2.7/site-packages/easy-install.pth
PYTHON_VERSION = $$(python -V 2>&1 | cut -f2 -d' ' | cut -f1,2 -d'.' --output-delimiter='')

.DEFAULT_GOAL = default
.PHONY: clean install install-virtual docs test dist deploy

default:
	@echo "Please choose one of the following targets: clean, install, install-virtual, docs, test, dist, requirements.txt"

clean:
	rm -rf "$(DIST)" "$(HTML)" .tox .coverage*
	-find . -maxdepth 1 -type f -name '.coverage' -delete
	-find . -maxdepth 1 -type d -name '.coverage' -exec rm -rf {} \; 2>/dev/null
	-find . -maxdepth 1 -type d -name 'build' -exec rm -rf {} \; 2>/dev/null

install:
	pip install .[ssh]

install-virtual:
	pip install --editable .[ssh]
	
	# "pip install --editable" will not add our extensions to the path, so we will patch the virtualenv
	EXTENSIONS_PATH="$$(head -n 1 "$(EASY_INSTALL_PTH)")/extensions" && \
	if ! grep -Fxq "$$EXTENSIONS_PATH" "$(EASY_INSTALL_PTH)"; then \
		echo "$$EXTENSIONS_PATH" >> "$(EASY_INSTALL_PTH)"; \
	fi

docs:
	pip install --requirement "$(DOCS)/requirements.txt"
	rm -rf "$(HTML)"
	sphinx-build -b html "$(DOCS)" "$(HTML)"

test:
	pip install --upgrade "tox>=2.7.0"
	tox -e pylint_code -e pylint_tests -e py$(PYTHON_VERSION) -e py$(PYTHON_VERSION)e2e -e py$(PYTHON_VERSION)ssh

dist: docs
	python ./setup.py sdist bdist_wheel
	# pushing LICENSE and additional files into the binary distribution archive
	-find "$(DIST)" -type f -name '*.whl' -exec zip -u {} LICENSE NOTICE DISCLAIMER \;

./requirements.txt: ./requirements.in
	pip install --upgrade "pip-tools>=1.9.0"
	pip-compile --output-file ./requirements.txt ./requirements.in
