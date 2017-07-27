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

HOSTNAME=$(ctx node capabilities host properties hostname)

# Change hostname
OLD_HOSTNAME=$(hostname)
if [ "$OLD_HOSTNAME" != "$HOSTNAME" ]; then
	hostname "$HOSTNAME"
	echo "$HOSTNAME" > /etc/hostname
	sed --in-place --expression "s/127.0.1.1\s\+$OLD_HOSTNAME/127.0.1.1 $HOSTNAME/" /etc/hosts
fi

ZONE=$(ctx service get_policy_by_type [ clearwater.Configuration ] properties zone)
GEOGRAPHICALLY_REDUNDANT=$(ctx service get_policy_by_type [ clearwater.Configuration ] properties geographically_redundant)
SITE_NAME=$(ctx service get_policy_by_type [ clearwater.Configuration ] properties site_name)
SECRET=$(ctx service get_policy_by_type [ clearwater.Configuration ] properties secret)

SMTP_HOSTNAME=$(ctx service get_node_by_type [ clearwater.Ellis ] get_outbound_relationship_by_name [ smtp ] target_node properties address)
SMTP_USERNAME=$(ctx service get_node_by_type [ clearwater.Ellis ] get_outbound_relationship_by_name [ smtp ] target_node capabilities smtp properties username)
SMTP_PASSWORD=$(ctx service get_node_by_type [ clearwater.Ellis ] get_outbound_relationship_by_name [ smtp ] target_node capabilities smtp properties password)

MAX_LOG_DIRECTORY_SIZE=$(ctx node capabilities host properties max_log_directory_size value)
REDUCE_CASSANDRA_MEM_USAGE=$(ctx node capabilities host properties reduce_cassandra_mem_usage)

PRIVATE_IP=$(ctx node attributes private_address)
PUBLIC_IP=$(ctx node attributes public_address)
PUBLIC_HOSTNAME=$(hostname)
# TODO: comma-separated list of all private IP addresses in group
ETCD_CLUSTER=$PRIVATE_IP

REPO_FILE=/etc/apt/sources.list.d/clearwater.list
REPO_LINE='deb http://repo.cw-ngv.com/stable binary/'
KEY_URL=http://repo.cw-ngv.com/repo_key


#
# Repository
#

if [ ! -f "$REPO_FILE" ]; then
	echo "$REPO_LINE" > "$REPO_FILE"
	curl --location "$KEY_URL" | apt-key add -
fi

apt update

if ! type aptdcon > /dev/null; then
	# This will allow us to do concurrent installs
	apt install aptdaemon --yes
fi

yes | aptdcon --hide-terminal --install clearwater-management


#
# DNS
#

S_CSCF_HOST="$PRIVATE_IP scscf.$PUBLIC_HOSTNAME # ARIA"
grep --quiet --fixed-strings "$S_CSCF_HOST" /etc/hosts || echo "$S_CSCF_HOST" >> /etc/hosts


#
# Local configuration
#

mkdir --parents /etc/clearwater
CONFIG_FILE=/etc/clearwater/local_config
echo "# Created by ARIA on $(date -u)" > "$CONFIG_FILE"

echo >> "$CONFIG_FILE"
echo "# Local IP configuration" >> "$CONFIG_FILE"
echo "local_ip=$PRIVATE_IP" >> "$CONFIG_FILE"
echo "public_ip=$PUBLIC_IP" >> "$CONFIG_FILE"
echo "public_hostname=$PUBLIC_HOSTNAME" >> "$CONFIG_FILE"
echo "etcd_cluster=$ETCD_CLUSTER" >> "$CONFIG_FILE"

if [ "$MAX_LOG_DIRECTORY_SIZE" != 0 ]; then
	echo >> "$CONFIG_FILE"
	echo "max_log_directory_size=$MAX_LOG_DIRECTORY_SIZE" >> "$CONFIG_FILE"
fi

if [ "$GEOGRAPHICALLY_REDUNDANT" = True ]; then
	echo >> "$CONFIG_FILE"
	echo "# Geographically redundant" >> "$CONFIG_FILE"
	echo "local_site_name=$SITE_NAME" >> "$CONFIG_FILE"

	# On the first Vellum node in the second site, you should set remote_cassandra_seeds to the
	# IP address of a Vellum node in the first site.
	#echo "remote_cassandra_seeds=" >> "$CONFIG_FILE"
fi


#
# Shared configuration
#

if [ "$GEOGRAPHICALLY_REDUNDANT" = True ]; then
	SPROUT_HOSTNAME=sprout.$SITE_NAME.$ZONE
	SPROUT_REGISTRATION_STORE=vellum.$SITE_NAME.$ZONE
	HS_HOSTNAME=hs.$SITE_NAME.$ZONE:8888
	HS_PROVISIONING_HOSTNAME=hs.$SITE_NAME.$ZONE:8889
	RALF_HOSTNAME=ralf.$SITE_NAME.$ZONE:10888
	RALF_SESSION_STORE=vellum.$ZONE
	XDMS_HOSTNAME=homer.$SITE_NAME.$ZONE:7888
	CHRONOS_HOSTNAME=vellum.$SITE_NAME.$ZONE
	CASSANDRA_HOSTNAME=vellum.$SITE_NAME.$ZONE
else
	VELLUM_IP=$PRIVATE_IP
	HOMESTEAD_IP=$PRIVATE_IP
	HOMER_IP=$PRIVATE_IP

	SPROUT_HOSTNAME=$PUBLIC_HOSTNAME
	SPROUT_REGISTRATION_STORE=$VELLUM_IP
	HS_HOSTNAME=$HOMESTEAD_IP:8888
	HS_PROVISIONING_HOSTNAME=$HOMESTEAD_IP:8889
	RALF_HOSTNAME=
	RALF_SESSION_STORE=
	XDMS_HOSTNAME=$HOMER_IP:7888
	CHRONOS_HOSTNAME=
	CASSANDRA_HOSTNAME=
fi

mkdir --parents /etc/clearwater
CONFIG_FILE=/etc/clearwater/shared_config
echo "# Created by ARIA on $(date -u)" > "$CONFIG_FILE"

echo >> "$CONFIG_FILE"
echo "# Deployment definitions" >> "$CONFIG_FILE"
echo "home_domain=$ZONE" >> "$CONFIG_FILE"
echo "sprout_hostname=$SPROUT_HOSTNAME" >> "$CONFIG_FILE"
echo "sprout_registration_store=$SPROUT_REGISTRATION_STORE" >> "$CONFIG_FILE"
echo "hs_hostname=$HS_HOSTNAME" >> "$CONFIG_FILE"
echo "hs_provisioning_hostname=$HS_PROVISIONING_HOSTNAME" >> "$CONFIG_FILE"
echo "ralf_hostname=$RALF_HOSTNAME" >> "$CONFIG_FILE"
echo "ralf_session_store=$RALF_SESSION_STORE" >> "$CONFIG_FILE"
echo "xdms_hostname=$XDMS_HOSTNAME" >> "$CONFIG_FILE"
echo "chronos_hostname=$CHRONOS_HOSTNAME" >> "$CONFIG_FILE"
echo "cassandra_hostname=$CASSANDRA_HOSTNAME" >> "$CONFIG_FILE"

echo >> "$CONFIG_FILE"
echo "# Email server configuration" >> "$CONFIG_FILE"
echo "smtp_smarthost=$SMTP_HOSTNAME" >> "$CONFIG_FILE"
echo "smtp_username=$SMTP_USERNAME" >> "$CONFIG_FILE"
echo "smtp_password=$SMTP_PASSWORD" >> "$CONFIG_FILE"
echo "email_recovery_sender=clearwater@$ZONE" >> "$CONFIG_FILE"

echo >> "$CONFIG_FILE"
echo "# I-CSCF/S-CSCF configuration (used by Bono to proxy to Sprout)" >> "$CONFIG_FILE"
echo "upstream_hostname=scscf.$HOSTNAME" >> "$CONFIG_FILE"

echo >> "$CONFIG_FILE"
echo "# Keys" >> "$CONFIG_FILE"
echo "signup_key=$SECRET" >> "$CONFIG_FILE"
echo "turn_workaround=$SECRET" >> "$CONFIG_FILE"
echo "ellis_api_key=$SECRET" >> "$CONFIG_FILE"
echo "ellis_cookie_key=$SECRET" >> "$CONFIG_FILE"

if [ "$REDUCE_CASSANDRA_MEM_USAGE" = True ]; then
	echo >> "$CONFIG_FILE"
	echo "# $REDUCE_CASSANDRA_MEM_USAGE" >> "$CONFIG_FILE"
	echo "reduce_cassandra_mem_usage=Y" >> "$CONFIG_FILE"
fi

# Copy to other hosts in etcd group
#yes | aptdcon --hide-terminal --install clearwater-config-manager
#cw-upload_shared_config
