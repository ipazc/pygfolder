==============
pygfpñder 0.0.4
==============

`PyGFolder` is a package for managing the Google Drive as a dictionary, with the same interface as PyFolder.

.. image:: https://badge.fury.io/py/pygfolder.svg
    :target: https://badge.fury.io/py/pygfolder

.. image:: https://travis-ci.org/ipazc/pygfolder.svg?branch=master
    :target: https://travis-ci.org/ipazc/pygfolder

.. image:: https://coveralls.io/repos/github/ipazc/pygfolder/badge.svg?branch=master
    :target: https://coveralls.io/github/ipazc/pygfolder?branch=master

.. image:: https://landscape.io/github/ipazc/pygfolder/master/landscape.svg?style=flat
   :target: https://landscape.io/github/ipazc/pygfolder/master
   :alt: Code Health


Installation
============
Currently it is only supported **Python 3.4.1** onwards:

.. code:: bash

    sudo pip3 install pygfolder


Example
=======
.. code:: python

    >>> from pygfolder import PyGFolder
    >>> 
    >>> pygfolder = PyGFolder("/path/to/folder")
    >>> pygfolder["file.txt"] = b"hello, this is going to be instantly the content of this file."
    >>> pygfolder["file.txt"]
    b"hello, this is going to be instantly the content of this file."


LICENSE
=======

It is released under the MIT license.
