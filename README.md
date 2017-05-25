ARIA
====

[![Build Status](https://travis-ci.org/apache/incubator-ariatosca.svg?branch=master)](https://travis-ci.org/apache/incubator-ariatosca)
[![Appveyor Build Status](https://ci.appveyor.com/api/projects/status/ltv89jk63ahiu306?svg=true)](https://ci.appveyor.com/project/ApacheSoftwareFoundation/incubator-ariatosca/history)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)


[ARIA](http://ariatosca.org/) is a an open-source, lightweight, library and CLI for orchestration that open-source projects can consume to build TOSCA-based orchestration solutions for resources and services orchestration. It supports NFV and hybrid Cloud scenarios. ARIA can be utilized by any organization that wants to implement TOSCA-based orchestration in its solutions, whether a multi-cloud enterprise application, or an NFV or SDN solution for multiple virtual infrastructure managers.

With ARIA, you can utilize TOSCA's cloud portability out-of-the-box, to test and run your applications, from blueprint to deployment, without having to also develop a TOSCA parser and execution engine. 

ARIA resides on your local host machine. Executions take place locally, but their output can occur anywhere.

ARIA adheres strictly to the
[TOSCA Simple Profile v1.0 cos01 specification](http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html),
providing state-of-the-art validation.

Validation errors include a plain English message and, when relevant, the exact location (file, row,
column) of the data that caused the error.

The ARIA API documentation always links to the relevant section of the specification. In addition, we provide an annotated version of the specification that links back to the API documentation.


Installing ARIA
----------------

You need Python 2.6 or 2.7. Python 3+ is not currently supported.

To install, we recommend using [pip](https://pip.pypa.io/) and a
[virtualenv](https://virtualenv.pypa.io/en/stable/).

In Ubuntu/Debian-based systems:

	sudo apt install python-setuptools
	sudo -H easy_install pip
	sudo -H pip install virtualenv
	virtualenv env

Or in Archlinux-based systems:

	pacman -S python2 python-setuptools python-pip
	pip install virtualenv
	virtualenv env -p $(type -p python2)

To install the latest development snapshot of ARIA:

	. env/bin/activate
	pip install git+http://git-wip-us.apache.org/repos/asf/incubator-ariatosca.git




Getting Started
---------------

You can use the following commands to utilize ARIA. A usage example is also provided at the end of this section.

* **`store`** Creates a service template.<br>
  **Usage** `aria service-templates store <template_name.yaml> <service_name>`
  
* **`create-archive`** Builds a CSAR archive. This archive format is unique to TOSCA.<br>
  **Usage** `aria services create <service_name> -t <template_hello>`
  
* **`reset`** Removes commands without removing any VM instances on which they were running. Requires the use of an **`-f`** flag.
  
* **`services`** Controls services by creating a logical instance of a service template. You can create multiple service templates, each with its own inputs, requirements and functionalities.<br>
  **Usage** `aria executions start install -s <service_name>`

* **`create-service`** Displays a graph after parsing is complete.

**"Hello World" Example**<br>
You can run the following commands to generate a "Hello World" example.

	# pip install git+https://github.com/apache/incubator-ariatosca.git
	# aria service-templates store <helloworld.yaml> <service_name>
	# aria services create <service_name> -t <template_hello>
	# aria executions start install -s <service_name>



Contribution
------------

You are welcome and encouraged to [contribute your feedback to the ARIA project](https://cwiki.apache.org/confluence/display/ARIATOSCA/Contributing+to+ARIA). Please review the guidelines at this link before submitting feedback.

Resources
---------
The following links provide access to ARIA resources.

* [ARIA home page](//http://ariatosca.org/)
* [wiki](https://cwiki.apache.org/confluence/display/AriaTosca)
* Mailing list: dev@ariatosca.incubator.apache.org
* [Bug Reports](https://issues.apache.org/jira/browse/ARIA)
* [Read-only Github mirror](https://github.com/apache/incubator-ariatosca/pulls)
* To contribute core and extensions code, [click here](https://cwiki.apache.org/confluence/display/ARIATOSCA/Contributing+Code)


License
-------
ARIA is licensed under the **Apache License 2.0**.

A permissive license whose main conditions require preservation of copyright and license notices. Contributors provide an express grant of patent rights. Licensed works, modifications, and larger works may be distributed under different terms and without source code.

