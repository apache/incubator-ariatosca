from aria import workflow
from aria.orchestrator.workflows.builtin import utils
from aria.orchestrator.workflows.exceptions import TaskException


INTERFACE_NAME = 'Maintenance'
ENABLE_OPERATION_NAME = 'enable'
DISABLE_OPERATION_NAME = 'disable'


@workflow
def maintenance(ctx, graph, enabled):
    """
    Custom workflow to call the operations on the Maintenance interface.
    """

    for node in ctx.model.node.iter():
        try:
            graph.add_tasks(utils.create_node_task(node=node,
                                                   interface_name=INTERFACE_NAME,
                                                   operation_name=ENABLE_OPERATION_NAME if enabled
                                                   else DISABLE_OPERATION_NAME))
        except TaskException:
            pass
