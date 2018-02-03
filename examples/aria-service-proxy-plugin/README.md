# ARIA Service Proxy Plugin

A plugin for inter-service coordination

## Types

### aria.serviceproxy.ServiceProxy
Abstract representation of an ARIA service.  The type operates by copying the outputs of target services into its local runtime attributes.  The service must be installed, and node properties control other conditions for successful instantiation.  It isn't assumed that the service exists at the time of instantiation, and properties control timeout behavior.  A failed service discovery, or listed desired outputs, results in a NonRecoverableError.  The plugin logic is entirely executed in the `create` lifecycle operation of the Standard interface.  Any template nodes dependent on the proxy will wait for the proxy to either gather the outputs of the target service, or timeout, which will abort the workflow.  The intended usage is for dependent nodes to have easy access to the outputs of ARIA managed services via attributes.

#### Properties
* __service_name__ : The name of the target service.  Required.
* __outputs__ : A `string` list of service outputs.  Acts as a filter to selected desired outputs. An empty list will result in no outputs being copied, which also would have the effect of making the existence of the target sufficient to satisfy the proxy.
* __wait_config__: A `dictionary` with two keys:
* * __wait_for_service__: A `boolean` that indicates whether to wait for a service that doesn't exist yet.  If `False`, if either the service or requested outputs are not present immediately, a non-recoverable exception is thrown.  If `True`, the plugin will wait.
* * __wait_time__: An `integer` that indicates the number of seconds to wait for the service, and specified outputs, to exist.  Beyond this time, a non-recoverable exception is thrown.  Note that there is no enforced maximum wait which could cause a misconfiguration to wait forever.
* * __wait_expression__: A Python evaluatable boolean expression using output names.  The expression acts as another barrier to matching the target service.  Examples values: "output1 > 4", "len(output1) == 7", "status == "ready"".  Be aware that while syntax is checked via Python evaluation, the meaning of the expression is not checked.  For example a wait expression of "1==0" could be supplied and result in an unsatifiable condition and wait (or failure).  Note that the Python evaluation environment only contains the target service outputs, and no additional imports.

#### Attributes
The outputs of the target are copied in a `list` in the runtime attributes named `service_outputs`.  Service outputs entries consist of single entry dictionaries, with the keys `name` and `value`.  Service output names and values are unchanged from their original values in the proxied service.
