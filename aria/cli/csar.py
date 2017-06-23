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
Support for the CSAR (Cloud Service ARchive) packaging specification.

See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
/TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html#_Toc461787381>`__
"""

import os
import logging
import pprint
import tempfile
import zipfile

import requests
from ruamel import yaml

CSAR_FILE_EXTENSION = '.csar'
META_FILE = 'TOSCA-Metadata/TOSCA.meta'
META_FILE_VERSION_KEY = 'TOSCA-Meta-File-Version'
META_FILE_VERSION_VALUE = '1.0'
META_CSAR_VERSION_KEY = 'CSAR-Version'
META_CSAR_VERSION_VALUE = '1.1'
META_CREATED_BY_KEY = 'Created-By'
META_CREATED_BY_VALUE = 'ARIA'
META_ENTRY_DEFINITIONS_KEY = 'Entry-Definitions'
BASE_METADATA = {
    META_FILE_VERSION_KEY: META_FILE_VERSION_VALUE,
    META_CSAR_VERSION_KEY: META_CSAR_VERSION_VALUE,
    META_CREATED_BY_KEY: META_CREATED_BY_VALUE,
}


def write(service_template_path, destination, logger):

    service_template_path = os.path.abspath(os.path.expanduser(service_template_path))
    source = os.path.dirname(service_template_path)
    entry = os.path.basename(service_template_path)

    meta_file = os.path.join(source, META_FILE)
    if not os.path.isdir(source):
        raise ValueError('{0} is not a directory. Please specify the service template '
                         'directory.'.format(source))
    if not os.path.isfile(service_template_path):
        raise ValueError('{0} does not exists. Please specify a valid entry point.'
                         .format(service_template_path))
    if os.path.exists(destination):
        raise ValueError('{0} already exists. Please provide a path to where the CSAR should be '
                         'created.'.format(destination))
    if os.path.exists(meta_file):
        raise ValueError('{0} already exists. This commands generates a meta file for you. Please '
                         'remove the existing metafile.'.format(meta_file))
    metadata = BASE_METADATA.copy()
    metadata[META_ENTRY_DEFINITIONS_KEY] = entry
    logger.debug('Compressing root directory to ZIP')
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as f:
        for root, _, files in os.walk(source):
            for file in files:
                file_full_path = os.path.join(root, file)
                file_relative_path = os.path.relpath(file_full_path, source)
                logger.debug('Writing to archive: {0}'.format(file_relative_path))
                f.write(file_full_path, file_relative_path)
        logger.debug('Writing new metadata file to {0}'.format(META_FILE))
        f.writestr(META_FILE, yaml.dump(metadata, default_flow_style=False))


class _CSARReader(object):

    def __init__(self, source, destination, logger):
        self.logger = logger
        if os.path.isdir(destination) and os.listdir(destination):
            raise ValueError('{0} already exists and is not empty. '
                             'Please specify the location where the CSAR '
                             'should be extracted.'.format(destination))
        downloaded_csar = '://' in source
        if downloaded_csar:
            file_descriptor, download_target = tempfile.mkstemp()
            os.close(file_descriptor)
            self._download(source, download_target)
            source = download_target
        self.source = os.path.expanduser(source)
        self.destination = os.path.expanduser(destination)
        self.metadata = {}
        try:
            if not os.path.exists(self.source):
                raise ValueError('{0} does not exists. Please specify a valid CSAR path.'
                                 .format(self.source))
            if not zipfile.is_zipfile(self.source):
                raise ValueError('{0} is not a valid CSAR.'.format(self.source))
            self._extract()
            self._read_metadata()
            self._validate()
        finally:
            if downloaded_csar:
                os.remove(self.source)

    @property
    def created_by(self):
        return self.metadata.get(META_CREATED_BY_KEY)

    @property
    def csar_version(self):
        return self.metadata.get(META_CSAR_VERSION_KEY)

    @property
    def meta_file_version(self):
        return self.metadata.get(META_FILE_VERSION_KEY)

    @property
    def entry_definitions(self):
        return self.metadata.get(META_ENTRY_DEFINITIONS_KEY)

    @property
    def entry_definitions_yaml(self):
        with open(os.path.join(self.destination, self.entry_definitions)) as f:
            return yaml.load(f)

    def _extract(self):
        self.logger.debug('Extracting CSAR contents')
        if not os.path.exists(self.destination):
            os.mkdir(self.destination)
        with zipfile.ZipFile(self.source) as f:
            f.extractall(self.destination)
        self.logger.debug('CSAR contents successfully extracted')

    def _read_metadata(self):
        csar_metafile = os.path.join(self.destination, META_FILE)
        if not os.path.exists(csar_metafile):
            raise ValueError('Metadata file {0} is missing from the CSAR'.format(csar_metafile))
        self.logger.debug('CSAR metadata file: {0}'.format(csar_metafile))
        self.logger.debug('Attempting to parse CSAR metadata YAML')
        with open(csar_metafile) as f:
            self.metadata.update(yaml.load(f))
        self.logger.debug('CSAR metadata:{0}{1}'.format(os.linesep, pprint.pformat(self.metadata)))

    def _validate(self):
        def validate_key(key, expected=None):
            if not self.metadata.get(key):
                raise ValueError('{0} is missing from the metadata file.'.format(key))
            actual = str(self.metadata[key])
            if expected and actual != expected:
                raise ValueError('{0} is expected to be {1} in the metadata file while it is in '
                                 'fact {2}.'.format(key, expected, actual))
        validate_key(META_FILE_VERSION_KEY, expected=META_FILE_VERSION_VALUE)
        validate_key(META_CSAR_VERSION_KEY, expected=META_CSAR_VERSION_VALUE)
        validate_key(META_CREATED_BY_KEY)
        validate_key(META_ENTRY_DEFINITIONS_KEY)
        self.logger.debug('CSAR entry definitions: {0}'.format(self.entry_definitions))
        entry_definitions_path = os.path.join(self.destination, self.entry_definitions)
        if not os.path.isfile(entry_definitions_path):
            raise ValueError('The entry definitions {0} referenced by the metadata file does not '
                             'exist.'.format(entry_definitions_path))

    def _download(self, url, target):
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise ValueError('Server at {0} returned a {1} status code'
                             .format(url, response.status_code))
        self.logger.info('Downloading {0} to {1}'.format(url, target))
        with open(target, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def read(source, destination=None, logger=None):
    destination = destination or tempfile.mkdtemp()
    logger = logger or logging.getLogger('dummy')
    return _CSARReader(source=source, destination=destination, logger=logger)


def is_csar_archive(source):
    return source.endswith(CSAR_FILE_EXTENSION)
