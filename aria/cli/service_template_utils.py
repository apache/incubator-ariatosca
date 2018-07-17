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

"""
Loading mechanism for service templates.
"""

import os
from urlparse import urlparse

from . import csar
from . import utils
from .exceptions import AriaCliError
from ..utils import archive as archive_utils


def get(source, service_template_filename):
    """
    Get a source and return a path to the main service template file

    The behavior based on then source argument content is:

    * local ``.yaml`` file: return the file
    * local archive (``.csar``, ``.zip``, ``.tar``, ``.tar.gz``, and ``.tar.bz2``): extract it
      locally and return path service template file
    * URL: download and get service template from downloaded archive
    * GitHub repo: download and get service template from downloaded archive

    :param source: path/URL/GitHub repo to archive/service-template file
    :type source: basestring
    :param service_template_filename: path to service template if source is a non-CSAR archive
     with CSAR archives, this is read from the metadata file)
    :type service_template_filename: basestring
    :return: path to main service template file
    :rtype: basestring
    """
    if urlparse(source).scheme:
        downloaded_file = utils.download_file(source)
        return _get_service_template_file_from_archive(
            downloaded_file, service_template_filename)
    elif os.path.isfile(source):
        if _is_archive(source):
            return _get_service_template_file_from_archive(source, service_template_filename)
        else:
            # Maybe check if yaml.
            return os.path.abspath(source)
    elif len(source.split('/')) == 2:
        url = _map_to_github_url(source)
        downloaded_file = utils.download_file(url)
        return _get_service_template_file_from_archive(
            downloaded_file, service_template_filename)
    else:
        raise AriaCliError(
            'You must provide either a path to a local file, a remote URL '
            'or a GitHub `organization/repository[:tag/branch]`')


def _get_service_template_file_from_archive(archive, service_template_filename):
    """
    Extract archive to temporary location and get path to service template file.

    :param archive: path to archive file
    :type archive: basestring
    :param service_template_filename: path to service template file relative to archive
    :type service_template_filename: basestring
    :return: absolute path to service template file
    :rtype: basestring

    """
    if csar.is_csar_archive(archive):
        service_template_file = _extract_csar_archive(archive)
    else:
        extract_directory = archive_utils.extract_archive(archive)
        service_template_dir = os.path.join(
            extract_directory,
            os.listdir(extract_directory)[0],
        )
        service_template_file = os.path.join(service_template_dir, service_template_filename)

    if not os.path.isfile(service_template_file):
        raise AriaCliError(
            'Could not find `{0}`. Please provide the name of the main '
            'service template file by using the `-n/--service-template-filename` flag'
            .format(service_template_filename))
    return service_template_file


def _map_to_github_url(source):
    """
    Returns a path to a downloaded GitHub archive.

    :param source: GitHub repo: ``org/repo[:tag/branch]``
    :type source: basestring
    :return: URL to the archive file for the given repo in GitHub
    :rtype: basestring

    """
    source_parts = source.split(':', 1)
    repo = source_parts[0]
    tag = source_parts[1] if len(source_parts) == 2 else 'master'
    url = 'https://github.com/{0}/archive/{1}.tar.gz'.format(repo, tag)
    return url


def _is_archive(source):
    return archive_utils.is_archive(source) or csar.is_csar_archive(source)


def _extract_csar_archive(archive):
    reader = csar.read(source=archive)
    main_service_template_file_name = reader.entry_definitions
    return os.path.join(reader.destination,
                        main_service_template_file_name)
