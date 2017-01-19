
from aria import workflow
from aria.orchestrator.workflows.api.task import OperationTask


@workflow
def maintenance(ctx, graph, enabled):
    """
    Custom workflow to call the operations on the Maintenance interface.
    """

    operation = 'Maintenance.enable' if enabled else 'Maintenance.disable'

    for node in ctx.model.node.iter():
        for interface in node.interfaces.filter_by(name='Maintenance', type_name='Maintenance'):
            graph.add_tasks(OperationTask.node(instance=node, name=operation))
