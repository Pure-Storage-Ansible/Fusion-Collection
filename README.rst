|License| |CLA-Assistant| |Code-style-black|

|Build history for master branch|

=======================================
Ansible Modules for Pure Storage Fusion
=======================================
Ansible Collection - purestorage.fusion
---------------------------------------

The fusion-ansible project provides an Ansible collection for managing and automating your Pure Storage Fusion environment. It consists of a set of modules for performing tasks related to Fusion.

This collection has been tested and supports Pure Storage Fusion 1.0.0.

*Note: This collection is not compatible with versions of Ansible before v2.11.*

Compatibility matrix
--------------------

.. list-table::
  :widths: 25 25 50
  :header-rows: 1
   
  * - Fusion version
    - Ansible "purestorage.fusion" version
    - Python "purefusion" version
    
  * - 1.0.0
    - 1.0.0
    - 1.0.1

*Notes*:

1. The "Python 'purefusion' version" column has the minimum recommended version used when testing the Ansible collection. This means you could use later versions of the Python "purefusion" than those listed.

Requirements
------------

- Ansible >= 2.11
- [Python PureFusion SDK]() v1.0.1 or newer
- Python >= 3.6, as the PureFusion SDK doesn't support Python version 2.x

Install
-------
Ansible must be installed (`Install guide <https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html>`_)

.. code-block:: python

  sudo pip install ansible


Python PureFusion SDK must be installed

.. code-block:: python

  sudo pip install purefusion

Install the collection (`Galaxy link <https://galaxy.ansible.com/purestorage/fusion>`_)

.. code-block:: python

  ansible-galaxy collection install purestorage.fusion

Contributing to this collection
-------------------------------
Ongoing development efforts and contributions to this collection are tracked as issues in this repository.

We welcome community contributions to this collection. If you find problems, need an enhancement or need a new module, please open an issue or create a PR against the `Pure Storage Fusion Ansible collection repository <https://github.com/Pure-Storage-Ansible/Fusion-Collection/issues>`_.

Code of Conduct
---------------
This collection follows the Ansible project's
`Code of Conduct <https://docs.ansible.com/ansible/devel/community/code_of_conduct.html>`_.
Please read and familiarize yourself with this document.

Releasing, Versioning and Deprecation
-------------------------------------
This collection follows `Semantic Versioning <https://semver.org>`_. More details on versioning can be found `in the Ansible docs <https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html#collection-versions>`_.

New minor and major releases as well as deprecations will follow new releases and deprecations of the Pure Storage Fusion product, its REST API and the corresponding Python SDK, which this project relies on. 

.. |License| image:: https://img.shields.io/badge/license-GPL%20v3.0-brightgreen.svg
   :target: COPYING.GPLv3
   :alt: Repository License
.. |CLA-Assistant| image:: https://cla-assistant.io/readme/badge/Pure-Storage-Ansible/Fusion-Collection
.. |Pure-Storage-Ansible-CI| image:: https://github.com/Pure-Storage-Ansible/Fusion-Collection/workflows/Pure%20Storage%20Ansible%20CI/badge.svg
.. |Code-style-black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. |Build history for master branch| image:: https://buildstats.info/github/chart/Pure-Storage-Ansible/Fusion-Collection?branch=master&buildCount=50&includeBuildsFromPullRequest=false&showstats=false
    :target: https://github.com/Pure-Storage-Ansible/Fusion-Collection/actions?query=branch%3Amaster
