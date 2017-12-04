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

from ...utils.formatting import (json_dumps, yaml_dumps)
from ..loading import UriLocation
from ..presentation import PresenterNotFoundError
from .consumer import Consumer


PRESENTATION_CACHE = {}
CANONICAL_LOCATION_CACHE = {}


class Read(Consumer):
    """
    Reads the presentation, handling imports recursively.

    It works by consuming a data source via appropriate :class:`~aria.parser.loading.Loader`,
    :class:`~aria.parser.reading.Reader`, and :class:`~aria.parser.presentation.Presenter`
    instances.

    It supports agnostic raw data composition for presenters that have
    ``_get_import_locations``, ``_validate_import``, and ``_merge_import``.

    To improve performance, loaders are called asynchronously on separate threads.

    Note that parsing may internally trigger more than one loading/reading/presentation
    cycle, for example if the agnostic raw data has dependencies that must also be parsed.
    """

    def __init__(self, context):
        super(Read, self).__init__(context)
        self._cache = {}

    def consume(self):
        # Present the main location and all imports recursively
        main_result, all_results = self._present_all()

        # Merge presentations
        main_result.merge(all_results, self.context)

        # Cache merged presentations
        if self.context.presentation.cache:
            for result in all_results:
                result.cache()

        self.context.presentation.presenter = main_result.presentation
        if main_result.canonical_location is not None:
            self.context.presentation.location = main_result.canonical_location

    def dump(self):
        if self.context.has_arg_switch('yaml'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.presentation.presenter._raw
            self.context.write(yaml_dumps(raw, indent=indent))
        elif self.context.has_arg_switch('json'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.presentation.presenter._raw
            self.context.write(json_dumps(raw, indent=indent))
        else:
            self.context.presentation.presenter._dump(self.context)

    def _handle_exception(self, e):
        if isinstance(e, _CancelPresentation):
            return
        super(Read, self)._handle_exception(e)

    def _present_all(self):
        """
        Presents all locations, including all nested imports, from the main location. Uses a thread
        pool executor for best performance.

        The main presentation is returned separately for easier access.
        """

        location = self.context.presentation.location

        if location is None:
            self.context.validation.report('Read consumer: missing location')
            return

        executor = self.context.presentation.create_executor()
        try:
            # This call may recursively submit tasks to the executor if there are imports
            main_result = self._present(location, None, None, executor)

            # Wait for all tasks to complete
            executor.drain()

            # Handle exceptions
            for e in executor.exceptions:
                self._handle_exception(e)

            all_results = executor.returns or []
        finally:
            executor.close()

        all_results.insert(0, main_result)

        return main_result, all_results

    def _present(self, location, origin_canonical_location, origin_presenter_class, executor):
        """
        Presents a single location. If the location has imports, those are submitted to the thread
        pool executor.

        Supports a presentation cache based on the canonical location as cache key.
        """

        # Link the context to this thread
        self.context.set_thread_local()

        # Canonicalize the location
        if self.context.reading.reader is None:
            loader, canonical_location = self._create_loader(location, origin_canonical_location)
        else:
            # If a reader is specified in the context then we skip loading
            loader = None
            canonical_location = location

        # Skip self imports
        if canonical_location == origin_canonical_location:
            raise _CancelPresentation()

        if self.context.presentation.cache:
            # Is the presentation in the global cache?
            try:
                presentation = PRESENTATION_CACHE[canonical_location]
                return _Result(presentation, canonical_location, origin_canonical_location)
            except KeyError:
                pass

        try:
            # Is the presentation in the local cache?
            presentation = self._cache[canonical_location]
            return _Result(presentation, canonical_location, origin_canonical_location)
        except KeyError:
            pass

        # Create and cache new presentation
        presentation = self._create_presentation(canonical_location, loader, origin_presenter_class)
        self._cache[canonical_location] = presentation

        # Submit imports to executor
        if hasattr(presentation, '_get_import_locations'):
            import_locations = presentation._get_import_locations(self.context)
            if import_locations:
                for import_location in import_locations:
                    import_location = UriLocation(import_location)
                    executor.submit(self._present, import_location, canonical_location,
                                    presentation.__class__, executor)

        return _Result(presentation, canonical_location, origin_canonical_location)

    def _create_loader(self, location, origin_canonical_location):
        loader = self.context.loading.loader_source.get_loader(self.context.loading, location,
                                                               origin_canonical_location)

        if origin_canonical_location is not None:
            # The cache key is is a combination of the canonical location of the origin, which is
            # globally absolute and never changes, and our location, which might be relative to
            # the origin's location
            cache_key = (origin_canonical_location, location)
            try:
                canonical_location = CANONICAL_LOCATION_CACHE[cache_key]
                return loader, canonical_location
            except KeyError:
                pass
        else:
            cache_key = None

        try:
            canonical_location = loader.get_canonical_location()
        except NotImplementedError:
            canonical_location = None

        # Because retrieving the canonical location can be costly, we will try to cache it
        if cache_key is not None:
            CANONICAL_LOCATION_CACHE[cache_key] = canonical_location

        return loader, canonical_location

    def _create_presentation(self, canonical_location, loader, default_presenter_class):
        # The reader we specified in the context will override
        reader = self.context.reading.reader

        if reader is None:
            # Read raw data from loader
            reader = self.context.reading.reader_source.get_reader(self.context.reading,
                                                                   canonical_location, loader)

        raw = reader.read()

        # Wrap raw data in presenter class
        if self.context.presentation.presenter_class is not None:
            # The presenter class we specified in the context will override
            presenter_class = self.context.presentation.presenter_class
        else:
            try:
                presenter_class = self.context.presentation.presenter_source.get_presenter(raw)
            except PresenterNotFoundError:
                if default_presenter_class is None:
                    raise
                else:
                    presenter_class = default_presenter_class

        if presenter_class is None:
            raise PresenterNotFoundError(u'presenter not found: {0}'.format(canonical_location))

        presentation = presenter_class(raw=raw)

        if hasattr(presentation, '_link_locators'):
            presentation._link_locators()

        return presentation


class _Result(object):
    """
    The result of a :meth:`Read._present` call. Contains the read presentation itself, as well as
    extra fields to help caching and keep track of merging.
    """

    def __init__(self, presentation, canonical_location, origin_canonical_location):
        self.presentation = presentation
        self.canonical_location = canonical_location
        self.origin_canonical_location = origin_canonical_location
        self.merged = False

    def get_imports(self, results):
        imports = []

        def has_import(result):
            for i in imports:
                if i.canonical_location == result.canonical_location:
                    return True
            return False

        for result in results:
            if result.origin_canonical_location == self.canonical_location:
                if not has_import(result):
                    imports.append(result)
        return imports

    def merge(self, results, context):
        # Make sure to only merge each presentation once
        if self.merged:
            return
        self.merged = True
        for result in results:
            if result.presentation == self.presentation:
                result.merged = True

        for result in self.get_imports(results):
            # Make sure import is merged
            result.merge(results, context)

            # Validate import
            if hasattr(self.presentation, '_validate_import'):
                if not self.presentation._validate_import(context, result.presentation):
                    # _validate_import will report an issue if invalid
                    continue

            # Merge import
            if hasattr(self.presentation, '_merge_import'):
                self.presentation._merge_import(result.presentation)

    def cache(self):
        if not self.merged:
            # Only merged presentations can be cached
            return
        PRESENTATION_CACHE[self.canonical_location] = self.presentation


class _CancelPresentation(Exception):
    pass
