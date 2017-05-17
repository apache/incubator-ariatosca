ARIA
====

[![Build Status](https://travis-ci.org/apache/incubator-ariatosca.svg?branch=master)](https://travis-ci.org/apache/incubator-ariatosca)
[![Appveyor Build Status](https://ci.appveyor.com/api/projects/status/ltv89jk63ahiu306?svg=true)](https://ci.appveyor.com/project/ApacheSoftwareFoundation/incubator-ariatosca/history)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)


[ARIA](http://ariatosca.org/) is a minimal TOSCA orchestrator, as well as a platform for building
TOSCA-based products. Its features can be accessed via a well-documented Python API.

On its own, ARIA provides built-in tools for blueprint validation and for creating ready-to-run
service instances. 

ARIA adheres strictly and meticulously to the
[TOSCA Simple Profile v1.0 cos01 specification](http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html),
providing state-of-the-art validation at seven different levels:

<ol start="0">
<li>Platform errors. E.g. network, hardware, or even an internal bug in ARIA (let us know,
	please!).</li>
<li>Syntax and format errors. E.g. non-compliant YAML, XML, JSON.</li>
<li>Field validation. E.g. assigning a string where an integer is expected, using a list instead of
	a dict.</li>
<li>Relationships between fields within a type. This is "grammar" as it applies to rules for
    setting the values of fields in relation to each other.</li>
<li>Relationships between types. E.g. referring to an unknown type, causing a type inheritance
    loop.</li>
<li>Topology. These errors happen if requirements and capabilities cannot be matched in order to
	assemble a valid topology.</li>
<li>External dependencies. These errors happen if requirement/capability matching fails due to
    external resources missing, e.g. the lack of a valid virtual machine, API credentials, etc.
    </li> 
</ol>

Validation errors include a plain English message and when relevant the exact location (file, row,
column) of the data the caused the error.

The ARIA API documentation always links to the relevant section of the specification, and likewise
we provide an annotated version of the specification that links back to the API documentation.


Quick Start
-----------

You need Python 2.6 or 2.7. Python 3+ is not currently supported.

To install, we recommend using [pip](https://pip.pypa.io/) and a
[virtualenv](https://virtualenv.pypa.io/en/stable/).

In Debian-based systems:

	sudo apt install python-setuptools
	sudo -H easy_install pip
	sudo -H pip install virtualenv
	virtualenv env --no-site-packages

Or in Archlinux-based systems:

	pacman -S python2 python-setuptools python-pip
	pip install virtualenv
	virtualenv env -p $(type -p python2) --no-site-packages

To install the latest development snapshot of ARIA:

	. env/bin/activate
	pip install git+http://git-wip-us.apache.org/repos/asf/incubator-ariatosca.git

To test it, let's create a service instance from a TOSCA blueprint:

	aria parse blueprints/tosca/node-cellar/node-cellar.yaml
	
You can also get it in JSON or YAML formats:

	aria parse blueprints/tosca/node-cellar/node-cellar.yaml --json

Or get an overview of the relationship graph:

	aria parse blueprints/tosca/node-cellar/node-cellar.yaml --graph

You can provide inputs as JSON, overriding default values provided in the blueprint

	aria parse blueprints/tosca/node-cellar/node-cellar.yaml --inputs='{"openstack_credential": {"user": "username"}}'

Instead of providing them explicitly, you can also provide them in a file or URL, in either JSON or
YAML. If you do so, the value must end in ".json" or ".yaml":

	aria parse blueprints/tosca/node-cellar/node-cellar.yaml --inputs=blueprints/tosca/node-cellar/inputs.yaml


CLI
---

Though ARIA is fully exposed as an API, it also comes with a CLI tool to allow you to work from the
shell:

	aria parse blueprints/tosca/node-cellar/node-cellar.yaml instance

The `parse` command supports the following directives to create variations of the default consumer
chain:

* `presentation`: emits a colorized textual representation of the Python presentation classes
   wrapping the blueprint.
* `model`: emits a colorized textual representation of the complete service model derived from the
   validated blueprint. This includes all the node templates, with their requirements satisfied at
   the level of relating to other node templates.
* `types`: emits a colorized textual representation of the type hierarchies.
* `instance`: **this is the default command**; emits a colorized textual representation of a
   service instance instantiated from the service model. Here the node templates are each used to
   create one or more nodes, with the appropriate relationships between them. Note that every time
   you run this consumer, you will get a different set of node IDs. Use `--graph` to see just the
   node relationship graph.
   
For all these commands, you can also use `--json` or `--yaml` flags to emit in those formats.

Additionally, The CLI tool lets you specify the complete classname of your own custom consumer to
chain at the end of the default consumer chain, after `instance`.

Your custom consumer can be an entry point into a powerful TOSCA-based tool or application, such as
an orchestrator, a graphical modeling tool, etc.


Development
-----------

Instead of installing with `pip`, it would be easier to work directly with the source files:

	pip install virtualenv
	virtualenv env
	. env/bin/activate
	git clone http://git-wip-us.apache.org/repos/asf/incubator-ariatosca.git ariatosca
	cd ariatosca
	pip install -e .

To run tests:

	pip install tox
	tox

Here's a quick example of using the API to parse YAML text into a service instance:

	from aria import install_aria_extensions
	from aria.parser.consumption import ConsumptionContext, ConsumerChain, Read, Validate, Model, Instance
	from aria.parser.loading import LiteralLocation
	
	def parse_text(payload, file_search_paths=[]):
	    context = ConsumptionContext()
	    context.presentation.location = LiteralLocation(payload)
	    context.loading.file_search_paths += file_search_paths
	    ConsumerChain(context, (Read, Validate, Model, Instance)).consume()
	    if not context.validation.dump_issues():
	        return context.modeling.instance
	    return None
	
	install_aria_extensions()

	print parse_text("""
	tosca_definitions_version: tosca_simple_yaml_1_0
	topology_template:
	  node_templates:
	    MyNode:
	      type: tosca.nodes.Compute 
	""")


Parser API Architecture
-----------------------

ARIA's parsing engine comprises individual "consumers" (in the `aria.parser.consumption` package)
that do things with blueprints. When chained together, each performs a different task, adds its own
validations, and can provide its own output.

Parsing happens in five phases, represented in five packages:

* `aria.parser.loading`: Loaders are used to read the TOSCA data, usually as text. For example
  UriTextLoader will load text from URIs (including files).
* `aria.parser.reading`: Readers convert data from the loaders into agnostic raw data. For
  example, `YamlReader` converts YAML text into Python dicts, lists, and primitives.
* `aria.parser.presentation`: Presenters wrap the agnostic raw data in a nice
  Python facade (a "presentation") that makes it much easier to work with the data, including
  utilities for validation, querying, etc. Note that presenters are _wrappers_: the agnostic raw
  data is always maintained intact, and can always be accessed directly or written back to files.
* `aria.parser.modeling.model`: Here the topology is normalized into a coherent structure of
  node templates, requirements, and capabilities. Types are inherited and properties are assigned.
  The service model is a _new_ structure, which is not mapped to the YAML. In fact, it is possible
  to generate the model programmatically, or from a DSL parser other than TOSCA.
* `aria.parser.modeling.instance`: The service instance is an instantiated service model. Node
  templates turn into node instances (with unique IDs), and requirements are satisfied by matching
  them to capabilities. This is where level 5 validation errors are detected (see above).

The phases do not have to be used in order. Indeed, consumers do not have to be used at all: ARIA
can be used to _produce_ blueprints. For example, it is possible to fill in the
`aria.parser.presentation` classes programmatically, in Python, and then write the presentation
to a YAML file as compliant TOSCA. The same technique can be used to convert from one DSL (consume
it) to another (write it).

The term "agnostic raw data" (ARD?) appears often in the documentation. It denotes data structures
comprising _only_ Python dicts, lists, and primitives, such that they can always be converted to and
from language-agnostic formats such as YAML, JSON, and XML. A considerable effort has been made to
conserve the agnostic raw data at all times. Thus, though ARIA makes good use of the dynamic power
of Python, you will _always_ be able to use ARIA with other systems.
