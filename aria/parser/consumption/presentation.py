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


from ..utils import FixedThreadPoolExecutor, json_dumps, yaml_dumps
from ..loading import UriLocation
from ..reading import AlreadyReadException
from ..presentation import PresenterNotFoundError
from .consumer import Consumer


class Read(Consumer):
    """
    Reads the presentation, handling imports recursively.

    It works by consuming a data source via appropriate :class:`aria.loader.Loader`,
    :class:`aria.reader.Reader`, and :class:`aria.presenter.Presenter` instances.

    It supports agnostic raw data composition for presenters that have
    :code:`_get_import_locations` and :code:`_merge_import`.

    To improve performance, loaders are called asynchronously on separate threads.

    Note that parsing may internally trigger more than one loading/reading/presentation
    cycle, for example if the agnostic raw data has dependencies that must also be parsed.
    """

    def consume(self):
        if self.context.presentation.location is None:
            self.context.validation.report('Presentation consumer: missing location')
            return

        presenter = None
        imported_presentations = None

        executor = FixedThreadPoolExecutor(size=self.context.presentation.threads,
                                           timeout=self.context.presentation.timeout)
        executor.print_exceptions = self.context.presentation.print_exceptions
        try:
            presenter = self._present(self.context.presentation.location, None, None, executor)
            executor.drain()

            # Handle exceptions
            for e in executor.exceptions:
                self._handle_exception(e)

            imported_presentations = executor.returns
        finally:
            executor.close()

        # Merge imports
        if (imported_presentations is not None) and hasattr(presenter, '_merge_import'):
            for imported_presentation in imported_presentations:
                okay = True
                if hasattr(presenter, '_validate_import'):
                    okay = presenter._validate_import(self.context, imported_presentation)
                if okay:
                    presenter._merge_import(imported_presentation)

        self.context.presentation.presenter = presenter

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
        if isinstance(e, AlreadyReadException):
            return
        super(Read, self)._handle_exception(e)

    def _present(self, location, origin_location, presenter_class, executor):
        # Link the context to this thread
        self.context.set_thread_local()

        raw = self._read(location, origin_location)

        if self.context.presentation.presenter_class is not None:
            # The presenter class we specified in the context overrides everything
            presenter_class = self.context.presentation.presenter_class
        else:
            try:
                presenter_class = self.context.presentation.presenter_source.get_presenter(raw)
            except PresenterNotFoundError:
                # We'll use the presenter class we were given (from the presenter that imported us)
                pass
            if presenter_class is None:
                raise PresenterNotFoundError('presenter not found')

        presentation = presenter_class(raw=raw)

        if presentation is not None and hasattr(presentation, '_link_locators'):
            presentation._link_locators()

        # Submit imports to executor
        if hasattr(presentation, '_get_import_locations'):
            import_locations = presentation._get_import_locations(self.context)
            if import_locations:
                for import_location in import_locations:
                    # The imports inherit the parent presenter class and use the current location as
                    # their origin location
                    import_location = UriLocation(import_location)
                    executor.submit(self._present, import_location, location, presenter_class,
                                    executor)

        return presentation

    def _read(self, location, origin_location):
        if self.context.reading.reader is not None:
            return self.context.reading.reader.read()
        loader = self.context.loading.loader_source.get_loader(self.context.loading, location,
                                                               origin_location)
        reader = self.context.reading.reader_source.get_reader(self.context.reading, location,
                                                               loader)
        return reader.read()
