
from aria import workflow
from aria.orchestrator.workflows.api.task import OperationTask


@workflow
def maintenance(ctx, graph, enabled):
    """
    Custom workflow to call the operations on the Maintenance interface.
    """

    operation = 'Maintenance.enable' if enabled else 'Maintenance.disable'

    for node_instance in ctx.model.node_instance.iter():
        if operation in node_instance.node.operations:
            task = OperationTask.node_instance(
                instance=node_instance,
                name=operation)
            graph.add_tasks(task)
