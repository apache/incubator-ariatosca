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


# This script is meant to help with the creation of Apache-compliant
# release candidates, as well as finalizing releases by using said candidates.
#
# Creation of a release candidate includes:
# 1) Creating a source package (a snapshot of the repository)
# 2) Creating a Pythonic sdist (generated docs, examples, etc., but no tests etc.)
# 3) Creating a Pythonic bdist (Wheel; binary distribution)
# 4) Publishing these packages on to https://dist.apache.org/repos/dist/dev/incubator/ariatosca/
# 5) Publishing the sdist and bdist packages on test-PyPI (https://test.pypi.org/)
#
# Finalization of a release includes:
# 1) Copying of the source, sdist and bdist packages from /dist/dev to /dist/release
#    (i.e. from https://dist.apache.org/repos/dist/dev/incubator/ariatosca/
#     to https://dist.apache.org/repos/dist/release/incubator/ariatosca/)
# 2) Publishing the sdist and bdist packages on PyPI (https://pypi.org)
# 3) Tagging the git repository for the release version
#
# Read more about Apache release rules and regulations at:
# 1) https://www.apache.org/dev/#releases
# 2) https://www.apache.org/legal/release-policy.html
# 3) https://www.apache.org/dev/release-distribution.html
# 4) https://www.apache.org/dev/release-publishing.html
# 5) https://www.apache.org/dev/release-signing.html
# 6) http://incubator.apache.org/incubation/Incubation_Policy.html#Releases
# 7) http://incubator.apache.org/guides/releasemanagement.html


set -e


function create_apache_release_candidate {
    if [ "$#" -lt 1 ]; then
        echo "Must provide git branch for release candidate" >&2
        return 1
    fi

    local GIT_BRANCH=$1
    local OPTIONAL_ARIATOSCA_DIST_DEV_PATH=$2

    ARIA_DIR=$(_get_aria_dir)
    pushd ${ARIA_DIR}

    git checkout ${GIT_BRANCH}
    local VERSION=$(cat VERSION)

    echo "Creating Apache release candidate for version ${VERSION}..."

    make clean
    _create_source_package ${GIT_BRANCH} ${VERSION}
    _create_sdist_and_bdist_packages
    _publish_to_apache_dev ${VERSION} ${OPTIONAL_ARIATOSCA_DIST_DEV_PATH}
    _publish_to_test_pypi
    git checkout -
    popd
}


function finalize_apache_release {
    if [ "$#" -ne 1 ]; then
        echo "Must provide git branch for release tagging" >&2
        return 1
    fi

    local GIT_BRANCH=$1

    ARIA_DIR=$(_get_aria_dir)
    pushd ${ARIA_DIR}

    git checkout ${GIT_BRANCH}
    local VERSION=$(cat VERSION)

    read -p "Enter 'Yes' to confirm release finalization for version ${VERSION}: " yn
    case $yn in
        Yes ) echo "Finalizing Apache release...";;
        * ) git checkout -; return;;
    esac

    _publish_to_apache_release ${VERSION}
    _publish_to_real_pypi
    _create_git_tag ${VERSION}
    git checkout -
    popd
}


function _get_aria_dir {
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    ARIA_DIR="$(dirname "${SCRIPT_DIR}")"
    echo ${ARIA_DIR}
}


function _create_source_package {
    local GIT_BRANCH=$1
    local VERSION=$2
    local INCUBATING_ARCHIVE_CONTENT_DIR=apache-ariatosca-${VERSION}-incubating  # e.g. apache-ariatosca-0.1.0-incubating
    local INCUBATING_ARCHIVE=${INCUBATING_ARCHIVE_CONTENT_DIR}.tar.gz  # e.g. apache-ariatosca-0.1.0-incubating.tar.gz
    local SOURCE_PACKAGE_DIR="source"

    echo "Creating source package..."
    mkdir -p dist/${SOURCE_PACKAGE_DIR}
    pushd dist/${SOURCE_PACKAGE_DIR}
    # re-cloning repository, to ensure repo snapshot is clean and not environment-dependent
    wget https://github.com/apache/incubator-ariatosca/archive/${GIT_BRANCH}.zip
    unzip ${GIT_BRANCH}.zip > /dev/null
    mv incubator-ariatosca-${GIT_BRANCH} ${INCUBATING_ARCHIVE_CONTENT_DIR}
    tar -czvf ${INCUBATING_ARCHIVE} ${INCUBATING_ARCHIVE_CONTENT_DIR} > /dev/null
    rm -rf ${INCUBATING_ARCHIVE_CONTENT_DIR}
    rm ${GIT_BRANCH}.zip

    _sign_package ${INCUBATING_ARCHIVE}
    popd
}

function _sign_package {
    local ARCHIVE_NAME=$1

    echo "Signing archive ${ARCHIVE_NAME}..."
    gpg --armor --output ${ARCHIVE_NAME}.asc --detach-sig ${ARCHIVE_NAME}
    gpg --print-md MD5 ${ARCHIVE_NAME} > ${ARCHIVE_NAME}.md5
    gpg --print-md SHA512 ${ARCHIVE_NAME} > ${ARCHIVE_NAME}.sha
}


function _create_sdist_and_bdist_packages {
    local SDIST_PACKAGE_DIR="sdist"
    local BDIST_PACKAGE_DIR="bdist"

    echo "Creating sdist and bdist packages..."
    make docs
    python setup.py sdist -d dist/${SDIST_PACKAGE_DIR} bdist_wheel -d dist/${BDIST_PACKAGE_DIR}

    # pushing LICENSE and additional files into the binary distribution archive
    find dist/${BDIST_PACKAGE_DIR} -type f -name '*.whl' -exec zip -u {} LICENSE NOTICE DISCLAIMER \;

    pushd dist/${SDIST_PACKAGE_DIR}
    local SDIST_ARCHIVE=$(find . -type f -name "*.tar.gz" -printf '%P\n')
    _sign_package ${SDIST_ARCHIVE}
    popd

    pushd dist/${BDIST_PACKAGE_DIR}
    local BDIST_ARCHIVE=$(find . -type f -name "*.whl" -printf '%P\n')
    _sign_package ${BDIST_ARCHIVE}
    popd
}


function _publish_to_test_pypi {
    echo "Publishing to test PyPI..."
    _publish_to_pypi https://test.pypi.org/legacy/
}


function _publish_to_apache_dev {
    local VERSION=$1
    local ARIATOSCA_DIST_DEV_PATH=$2

    local DIST_DIR=$(pwd)/dist
    local RELEASE_DIR=${VERSION}-incubating  # e.g. 0.1.0-incubating

    echo "Publishing to Apache dist dev..."
    if [ -z "${ARIATOSCA_DIST_DEV_PATH}" ]; then
        local TMP_DIR=$(mktemp -d)
        echo "Checking out ARIA dist dev to ${TMP_DIR}"
        pushd ${TMP_DIR}
        svn co https://dist.apache.org/repos/dist/dev/incubator/ariatosca/
        popd
        pushd ${TMP_DIR}/ariatosca
    else
        pushd ${ARIATOSCA_DIST_DEV_PATH}
    fi

    svn up
    cp -r ${DIST_DIR} .
    mv dist/ ${RELEASE_DIR}/
    svn add ${RELEASE_DIR}
    svn commit -m "ARIA ${VERSION} release candidate"
    popd
}


function _publish_to_real_pypi {
    echo "Publishing to PyPI..."
    _publish_to_pypi https://upload.pypi.org/legacy/
}


function _publish_to_pypi {
    local REPOSITORY_URL=$1

    pushd dist

    pushd sdist
    local SDIST_ARCHIVE=$(find . -type f -name "*.tar.gz" -printf '%P\n')
    twine upload --repository-url ${REPOSITORY_URL} ${SDIST_ARCHIVE} ${SDIST_ARCHIVE}.asc
    popd

    pushd bdist
    local BDIST_ARCHIVE=$(find . -type f -name "*.whl" -printf '%P\n')
    twine upload --repository-url ${REPOSITORY_URL} ${BDIST_ARCHIVE} ${BDIST_ARCHIVE}.asc
    popd

    popd
}


function _publish_to_apache_release {
    local VERSION=$1
    local RELEASE_DIR=${VERSION}-incubating  # e.g. 0.1.0-incubating

    echo "Publishing to Apache dist..."

    local TMP_DIR=$(mktemp -d)
    echo "Checking out ARIA dist dev to ${TMP_DIR}"
    pushd ${TMP_DIR}

    svn co https://dist.apache.org/repos/dist/dev/incubator/ariatosca/ ariatosca-dev
    svn co https://dist.apache.org/repos/dist/release/incubator/ariatosca/ ariatosca-release
    cp -r ariatosca-dev/${RELEASE_DIR} ariatosca-release

    pushd ariatosca-release
    svn add ${RELEASE_DIR}
    # TODO: remove older releases?
    svn commit -m "ARIA ${VERSION} release"
    popd
    popd
}


function _create_git_tag {
    local VERSION=$1

    echo "Creating git tag ${VERSION}"
    git tag -a ${VERSION} -m "ARIA ${VERSION}"
    git push --tags origin
}


function pushd {
    command pushd "$@" > /dev/null
}



function popd {
    command popd "$@" > /dev/null
}



if [ "$#" -ne 2 ]; then
    echo "Usage: $0 {candidate,package} <git-branch>" >&2
    exit 1
fi

OPERATION=$1
GIT_BRANCH=$2

if [ "${OPERATION}" == "candidate" ]; then
    create_apache_release_candidate ${GIT_BRANCH}
elif [ "${OPERATION}" == "package" ]; then
    finalize_apache_release ${GIT_BRANCH}
else
    echo "First parameter must be either 'candidate' or 'package'" >&2
    exit 1
fi
