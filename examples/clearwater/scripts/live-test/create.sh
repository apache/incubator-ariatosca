#!/bin/bash
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

set -e

LIB=/opt/clearwater-live-test
COMMAND=/usr/bin/clearwater-live-test
RUBY_VERSION=1.9.3
RVM=/usr/local/rvm
QUAFF_OLD_URL=git@github.com:metaswitch/quaff.git
QUAFF_NEW_URL=https://github.com/Metaswitch/quaff.git

# Build requirements
yes | aptdcon --hide-terminal --install build-essential
yes | aptdcon --hide-terminal --install bundler
yes | aptdcon --hide-terminal --install git

# Required by nokogiri Ruby gem
yes | aptdcon --hide-terminal --install zlib1g-dev

# Install Ruby enVironment Manager
if [ ! -d "$RVM" ]; then
	# Install
	curl --location https://get.rvm.io | bash -s stable
fi

# Install Ruby using RVM
. "$RVM/scripts/rvm"
rvm autolibs enable
rvm install "$RUBY_VERSION"
rvm use "$RUBY_VERSION@global"

# Install Clearwater Live Test
if [ ! -d "$LIB" ]; then
	mkdir --parents /opt
	cd /opt
	git clone --depth 1 https://github.com/Metaswitch/clearwater-live-test.git
	cd clearwater-live-test
	chmod a+rw -R .

	# Note: we must fix the URLs for Quaff
	sed --in-place --expression "s,$QUAFF_OLD_URL,$QUAFF_NEW_URL,g" Gemfile Gemfile.lock

	# Install required Ruby gems 
	bundle install
fi

# Create command
echo "#!/bin/bash" > "$COMMAND"
echo ". \"$RVM/scripts/rvm\"" >> "$COMMAND"
echo "rvm use \"$RUBY_VERSION@global\"" >> "$COMMAND"
echo "cd \"$LIB\"" >> "$COMMAND"
echo "rake \"\$@\"" >> "$COMMAND"
chmod a+x "$COMMAND"

# clearwater-live-test test[example.com] SIGNUP_CODE=secret PROXY=192.168.1.171 ELLIS=192.168.1.171
