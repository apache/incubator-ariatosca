ARIA
====

|Build Status| |Appveyor Build Status| |License| |PyPI release| |Python Versions| |Wheel|
|Contributors| |Open Pull Requests| |Closed Pull Requests|


What is ARIA?
-------------

`ARIA <http://ariatosca.incubator.apache.org/>`__ is a an open-source,
`TOSCA <https://www.oasis-open.org/committees/tosca/>`__-based, lightweight library and CLI for
orchestration and for consumption by projects building TOSCA-based solutions for resources and
services orchestration.

ARIA can be utilized by any organization that wants to implement TOSCA-based orchestration in its
solutions, whether a multi-cloud enterprise application, or an NFV or SDN solution for multiple
virtual infrastructure managers.

With ARIA, you can utilize TOSCA's cloud portability out-of-the-box, to develop, test and run your
applications, from template to deployment.

ARIA is an incubation project under the `Apache Software Foundation <https://www.apache.org/>`__.


Installation
------------

ARIA is `available on PyPI <https://pypi.python.org/pypi/apache-ariatosca>`__.

ARIA requires Python 2.6/2.7. Python 3 is currently not supported.

To install ARIA directly from PyPI (using a ``wheel``), use::

    pip install --upgrade pip setuptools
    pip install apache-ariatosca

To install ARIA from source, download the source tarball from
`PyPI <https://pypi.python.org/pypi/apache-ariatosca>`__, extract and ``cd`` into the extract dir,
and run::

    pip install --upgrade pip setuptools
    pip install .

| The source package comes along with relevant examples, documentation, ``requirements.txt`` (for
| installing specifically the frozen dependencies' versions with which ARIA was tested) and more.
|
| ARIA has additional optional dependencies. These are required for running operations over SSH.
| Below are instructions on how to install these dependencies, including required system
| dependencies per OS.
|
| Note: These dependencies may have varying licenses which may not be compatible with Apache license
| 2.0.

**Ubuntu/Debian** (tested on Ubuntu 14.04, Ubuntu 16.04)::

    apt-get install -y python-dev gcc libffi-dev libssl-dev
    pip install apache-ariatosca[ssh]

**CentOS/Fedora** (tested on CentOS 6.6, CentOS 7)::

    yum install -y python-devel gcc libffi-devel openssl-devel
    pip install apache-ariatosca[ssh]

**Archlinux**::

    pacman -Syu --noconfirm python2 gcc libffi openssl
    pip2 install apache-ariatosca[ssh]

**Windows** (tested on Windows 10)::

    # no additional system requirements are needed
    pip install apache-ariatosca[ssh]

**MacOS**::

    # TODO



To install ``pip``, either use your operating system's package management system, or run::

    wget http://bootstrap.pypa.io/get-pip.py
    python get-pip.py



Getting Started
---------------

This section will describe how to run a simple "Hello World" example.

First, provide ARIA with the ARIA "hello world" service-template and name it (e.g.
``my-service-template``)::

    aria service-templates store examples/hello-world/hello-world.yaml my-service-template

Now create a service based on this service-template and name it (e.g. ``my-service``)::

    aria services create my-service -t my-service-template

Finally, start an ``install`` workflow execution on ``my-service`` like so::

    aria executions start install -s my-service

You should now have a simple web-server running on your local machine. You can try visiting
``http://localhost:9090`` to view your deployed application.

To uninstall and clean your environment, follow these steps::

    aria executions start uninstall -s my-service
    aria services delete my-service
    aria service-templates delete my-service-template


Contribution
------------

You are welcome and encouraged to participate and contribute to the ARIA project.

Please see our guide to
`Contributing to ARIA
<https://cwiki.apache.org/confluence/display/ARIATOSCA/Contributing+to+ARIA>`__.

Feel free to also provide feedback on the mailing lists (see `Resources <#user-content-resources>`__
section).


Resources
---------

- `ARIA homepage <http://ariatosca.incubator.apache.org/>`__
- `ARIA wiki <https://cwiki.apache.org/confluence/display/AriaTosca>`__
-  `Issue tracker <https://issues.apache.org/jira/browse/ARIA>`__
- `ARIA revisions released <https://dist.apache.org/repos/dist/dev/incubator/ariatosca//>`__

- Dev mailing list: dev@ariatosca.incubator.apache.org
- User mailing list: user@ariatosca.incubator.apache.org

Subscribe by sending a mail to ``<group>-subscribe@ariatosca.incubator.apache.org`` (e.g.
``dev-subscribe@ariatosca.incubator.apache.org``). See information on how to subscribe to mailing
lists `here <https://www.apache.org/foundation/mailinglists.html>`__.

For past correspondence, see the
`dev mailing list archive <https://lists.apache.org/list.html?dev@ariatosca.apache.org>`__.


License
-------

ARIA is licensed under the
`Apache License 2.0 <https://github.com/apache/incubator-ariatosca/blob/master/LICENSE>`__.

.. |Build Status| image:: https://img.shields.io/travis/apache/incubator-ariatosca/master.svg
   :target: https://travis-ci.org/apache/incubator-ariatosca
.. |Appveyor Build Status| image:: https://img.shields.io/appveyor/ci/ApacheSoftwareFoundation/incubator-ariatosca/master.svg
   :target: https://ci.appveyor.com/project/ApacheSoftwareFoundation/incubator-ariatosca/history
.. |License| image:: https://img.shields.io/github/license/apache/incubator-ariatosca.svg
   :target: http://www.apache.org/licenses/LICENSE-2.0
.. |PyPI release| image:: https://img.shields.io/pypi/v/apache-ariatosca.svg
   :target: https://pypi.python.org/pypi/apache-ariatosca
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/apache-ariatosca.svg
.. |Wheel| image:: https://img.shields.io/pypi/wheel/apache-ariatosca.svg
.. |Contributors| image:: https://img.shields.io/github/contributors/apache/incubator-ariatosca.svg
.. |Open Pull Requests| image:: https://img.shields.io/github/issues-pr/apache/incubator-ariatosca.svg
   :target: https://github.com/apache/incubator-ariatosca/pulls
.. |Closed Pull Requests| image:: https://img.shields.io/github/issues-pr-closed-raw/apache/incubator-ariatosca.svg
   :target: https://github.com/apache/incubator-ariatosca/pulls?q=is%3Apr+is%3Aclosed
