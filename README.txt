          Celestica Complex Analytic Test Tool
                    Version 0.0.1
Introduction
============
Pycat is a complex analytic test tool written in python.

Install
=======
* Install from source package.
  Unpack the source pacakge.
  $ tar zxvf pycat-version.tar.gz
  GO to the unpacked directory.
  $ cd pycat-version
  Run installation.
  $ python setup.py install

* Other installations.
  Pycat only support installing from source packages by now.

Installed Files
===============
* Pycat Config
  The config files are installed under /usr/etc/pycat.
    - pycat.xml The system config of pycat.
    - Each plugin creates a sub-directory under /usr/etc/pycat.

* Python Modules
  The directory which pycat module is installed depends on the python version
  you are using. Generally you can find a directory named 'site-packages'
  under your python. For example, if you are using Fedora 19, it installs
  under '/usr/lib/python2.7/site-packages/'.
  The following modules are avaliable now:
  - pycat.log
  - pycat.config
  - pycat.testcase

* Command Line Interface
  Pycat support some CLIs, which installs under /usr/bin
  - cat-session

