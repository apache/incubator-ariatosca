# ARIA Service Proxy Plugin

A plugin for inter-service coordination

## Types

### aria.serviceproxy.ServiceProxy
Abstract representation of an ARIA service.  The type operates by copying the outputs of target services into its local runtime attributes.  The service must be installed, and node properties control other conditions for successful instantiation.  It isn't assumed that the service exists at the time of instantiation, and properties control timeout behavior.  A failed service discovery, or listed desired outputs, results in a NonRecoverableError.

#### Properties
* __service_name__ : The name of the target service.
* __outputs__ : A `string` list of service outputs.  Acts as a filter to selected desired outputs. An empty list will result in no outputs being copied.
* __wait_config__: A `dictionary` with two keys:
* * __wait_for_service__: A `boolean` that indicates whether to wait for a service that doesn't exist yet.  If `False`, if either the service or requested outputs are not present immediately, a non-recoverable exception is thrown.  If `True`, the plugin will wait.
* * __wait_time__: An `integer` that indicates the number of seconds to wait for the service, and specified outputs, to exist.  Beyond this time, a non-recoverable exception is thrown.
* * __wait_expression__: A Python evaluatable boolean expression using output names.  The expression acts as another barrier to matching the target service.  Examples values: "output1 > 4", "len(output1) == 7", "status == "ready"".

#### Attributes
The outputs of the target are placed in a `list` in the runtime attributes named `service_outputs`.  Service outputs entries consist of single entry dictionaries, with the keys `name` and `value`.
