import logging
from aria.modeling import models
from mock import MagicMock

from tests.mock import models as mock_models


def setup_logger(logger_name,
                 level=logging.INFO,
                 handlers=None,
                 remove_existing_handlers=True,
                 logger_format=None,
                 propagate=True):
    """
    :param logger_name: Name of the logger.
    :param level: Level for the logger (not for specific handler).
    :param handlers: An optional list of handlers (formatter will be
                     overridden); If None, only a StreamHandler for
                     sys.stdout will be used.
    :param remove_existing_handlers: Determines whether to remove existing
                                     handlers before adding new ones
    :param logger_format: the format this logger will have.
    :param propagate: propagate the message the parent logger.
    :return: A logger instance.
    :rtype: logging.Logger
    """

    logger = logging.getLogger(logger_name)

    if remove_existing_handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    for handler in handlers:
        if logger_format:
            formatter = logging.Formatter(fmt=logger_format)
            handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    if not propagate:
        logger.propagate = False

    return logger


class MockStorage(object):

    def __init__(self):
        self.service_template = MockServiceTemplateStorage()
        self.service = MockServiceStorage()
        self.node_template = MockNodeTemplateStorage()
        self.node = MockNodeStorage()


class MockServiceTemplateStorage(object):

    def __init__(self):
        self.list = MagicMock(return_value=[mock_models.create_service_template('test_st')])

    @staticmethod
    def get_by_name(name):
        st = mock_models.create_service_template('test_st')
        if name == 'no_services_no_description':
            pass
        elif name == 'no_services_yes_description':
            st.description = 'test_description'
        elif name == 'one_service_no_description':
            service = mock_models.create_service(st, 'test_s')
            st.services = [service]
        elif name == 'one_service_yes_description':
            service = mock_models.create_service(st, 'test_s')
            st.description = 'test_description'
            st.services = [service]
        elif name == 'with_inputs':
            input = mock_models.create_parameter(name='input1', value='value1')
            st.inputs = {'input1': input}
        elif name == 'without_inputs':
            st.inputs = {}
        elif name == 'one_service':
            service = mock_models.create_service(st, 'test_s')
            st.services = [service]
        return st


class MockServiceStorage(object):

    def __init__(self):
        self.st = mock_models.create_service_template('test_st')
        self.list = MagicMock(return_value=[mock_models.create_service(self.st, 'test_s')])
        self.delete = MagicMock()

    @staticmethod
    def get(id):
        test_st = mock_models.create_service_template('test_st')
        test_s = mock_models.create_service(test_st, 'test_s')
        if id == '1':
            execution = mock_models.create_execution(test_s, status=models.Execution.STARTED)
            execution.id = '1'
            test_s.executions = [execution]
        elif id == '2':
            node_template = mock_models.create_node_template(service_template=test_st)
            node = mock_models.create_node(name='test_node',
                                           dependency_node_template=node_template,
                                           service=test_s,
                                           state=models.Node.STARTED)
            node.id = '1'
        return test_s

    @staticmethod
    def get_by_name(name):
        test_st = mock_models.create_service_template('test_st')
        test_s = mock_models.create_service(test_st, 'test_s')
        if name == 'service_with_active_executions':
            m = MagicMock()
            m.id = '1'
            return m
        elif name == 'service_with_available_nodes':
            m = MagicMock()
            m.id = '2'
            return m
        elif name == 'service_with_no_inputs':
            pass
        elif name == 'service_with_one_input':
            input = mock_models.create_parameter(name='input1', value='value1')
            test_s.inputs = {'input1': input}

        return test_s


class MockNodeTemplateStorage(object):

    def __init__(self):
        self.st = mock_models.create_service_template('test_st')
        self.list = MagicMock(return_value=[mock_models.create_node_template(self.st, 'test_nt')])


    @staticmethod
    def get(id):
        st = mock_models.create_service_template('test_st')
        s = mock_models.create_service(st, 'test_s')
        nt = mock_models.create_node_template(service_template=st, name='test_nt')
        if id == '1':
            pass
        elif id == '2':
            prop1 = mock_models.create_parameter('prop1', 'value1')
            nt.properties = {'prop1': prop1}
        elif id == '3':
            mock_models.create_node('node1', nt, s)
        elif id == '4':
            prop1 = mock_models.create_parameter('prop1', 'value1')
            nt.properties = {'prop1': prop1}
            mock_models.create_node('node1', nt, s)
        return nt


class MockNodeStorage(object):

    def __init__(self):
        self.st = mock_models.create_service_template('test_st')
        self.s = mock_models.create_service(self.st, 'test_s')
        self.nt = mock_models.create_node_template(service_template=self.st, name='test_nt')
        self.list = MagicMock(return_value=[mock_models.create_node('test_n', self.nt, self.s)])

    @staticmethod
    def get(id):
        st = mock_models.create_service_template('test_st')
        s = mock_models.create_service(st, 'test_s')
        nt = mock_models.create_node_template(service_template=st, name='test_nt')
        n = mock_models.create_node('test_n', nt, s)
        if id == '1':
            pass
        elif id == '2':
            n.runtime_properties = {'attribute1': 'value1'}
        return n
