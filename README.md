ARIA
====

[![Build Status](https://img.shields.io/travis/apache/incubator-ariatosca/master.svg)](https://travis-ci.org/apache/incubator-ariatosca)
[![Appveyor Build Status](https://img.shields.io/appveyor/ci/ApacheSoftwareFoundation/incubator-ariatosca/master.svg)](https://ci.appveyor.com/project/ApacheSoftwareFoundation/incubator-ariatosca/history)
[![License](https://img.shields.io/github/license/apache/incubator-ariatosca.svg)](http://www.apache.org/licenses/LICENSE-2.0)
[![PyPI release](https://img.shields.io/pypi/v/ariatosca.svg)](https://pypi.python.org/pypi/ariatosca)
![Python Versions](https://img.shields.io/pypi/pyversions/ariatosca.svg)
![Wheel](https://img.shields.io/pypi/wheel/ariatosca.svg)
![Contributors](https://img.shields.io/github/contributors/apache/incubator-ariatosca.svg)
[![Open Pull Requests](https://img.shields.io/github/issues-pr/apache/incubator-ariatosca.svg)](https://github.com/apache/incubator-ariatosca/pulls)
[![Closed Pull Requests](https://img.shields.io/github/issues-pr-closed-raw/apache/incubator-ariatosca.svg)](https://github.com/apache/incubator-ariatosca/pulls?q=is%3Apr+is%3Aclosed)


What is ARIA?
----------------

[ARIA](http://ariatosca.incubator.apache.org/) is a an open-source, [TOSCA](https://www.oasis-open.org/committees/tosca/)-based, lightweight library and CLI for orchestration and for consumption by projects building TOSCA-based solutions for resources and services orchestration.

ARIA can be utilized by any organization that wants to implement TOSCA-based orchestration in its solutions, whether a multi-cloud enterprise application, or an NFV or SDN solution for multiple virtual infrastructure managers.

With ARIA, you can utilize TOSCA's cloud portability out-of-the-box, to develop, test and run your applications, from template to deployment.

ARIA is an incubation project under the [Apache Software Foundation](https://www.apache.org/).


Installation
----------------

ARIA is [available on PyPI](https://pypi.python.org/pypi/ariatosca).    

To install ARIA directly from PyPI (using a `wheel`), use:

    pip install aria


To install ARIA from source, download the source tarball from [PyPI](https://pypi.python.org/pypi/ariatosca),
extract it, and then when inside the extracted directory, use:

    pip install .

The source package comes along with relevant examples, documentation,
`requirements.txt` (for installing specifically the frozen dependencies' versions with which ARIA was tested) and more.

<br>
Note that for the `pip install` commands mentioned above, you must use a privileged user, or use virtualenv.
<br><br><br>

ARIA itself is in a `wheel` format compatible with all platforms. 
Some dependencies, however, might require compilation (based on a given platform), and therefore possibly some system dependencies are required as well.

On Ubuntu or other Debian-based systems:

	sudo apt install python-setuptools python-dev build-essential libssl-dev libffi-dev

On Archlinux:

	sudo pacman -S python-setuptools


ARIA requires Python 2.6/2.7. Python 3+ is currently not supported.


Getting Started
---------------

This section will describe how to run a simple "Hello World" example.

First, provide ARIA with the ARIA "hello world" service-template and name it (e.g. `my-service-template`):

	aria service-templates store examples/hello-world/helloworld.yaml my-service-template
	
Now create a service based on this service-template and name it (e.g. `my-service`):
	
	aria services create my-service -t my-service-template
	
Finally, start an `install` workflow execution on `my-service` like so:

	aria executions start install -s my-service

<br>
You should now have a simple web-server running on your local machine.
You can try visiting http://localhost:9090 to view your deployed application.

To uninstall and clean your environment, follow these steps:

    aria executions start uninstall -s my-service
    aria services delete my-service
    aria service-templates delete my-service-template


Contribution
------------

You are welcome and encouraged to participate and contribute to the ARIA project.

Please see our guide to [Contributing to ARIA](https://cwiki.apache.org/confluence/display/ARIATOSCA/Contributing+to+ARIA).

Feel free to also provide feedback on the mailing lists (see [Resources](#user-content-resources) section).


Resources
---------

* [ARIA homepage](http://ariatosca.incubator.apache.org/)
* [ARIA wiki](https://cwiki.apache.org/confluence/display/AriaTosca)
* [Issue tracker](https://issues.apache.org/jira/browse/ARIA)

* Dev mailing list: dev@ariatosca.incubator.apache.org
* User mailing list: user@ariatosca.incubator.apache.org

Subscribe by sending a mail to `<group>-subscribe@ariatosca.incubator.apache.org` (e.g. `dev-subscribe@ariatosca.incubator.apache.org`).
See information on how to subscribe to mailing list [here](https://www.apache.org/foundation/mailinglists.html).

For past correspondence, see the [dev mailing list archive](http://mail-archives.apache.org/mod_mbox/incubator-ariatosca-dev/).


License
-------
ARIA is licensed under the [Apache License 2.0](https://github.com/apache/incubator-ariatosca/blob/master/LICENSE).
