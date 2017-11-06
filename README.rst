===============
pygfolder 0.0.5
===============

`PyGFolder` is a package for managing the Google Drive content as a Python dictionary, with the same interface as `PyFolder <https://pypi.python.org/pypi/pyfolder>`_.

.. image:: https://badge.fury.io/py/pygfolder.svg
    :target: https://badge.fury.io/py/pygfolder

An easy example of usage is as follows:

.. code:: python

    >>> from pygfolder import PyGFolder
    >>>
    >>> pygfolder = PyGFolder("/path/to/GoogleDrive/folder")
    >>> pygfolder["file.txt"] = b"hello, this is going to be instantly the content of this file."
    >>> pygfolder["file.txt"]
    b"hello, this is going to be instantly the content of this file."


`PyGFolder` allows to create/edit/remove elements from the google drive as if it was a Python Dict.

Installation
============

Currently, it is only supported **Python 3.4.1** onwards:

.. code:: bash

    sudo pip3 install pygfolder

It requires the credentials file generated at https://console.developers.google.com within your Google Drive account. Once you have generated the credentials for the Google Drive API (it is going to be a JSON file containing the OAUTH2 parameters such as *client_id*, *project_id*, *client_secret*, *auth_uri*, *...*), download the file and save it in your `$HOME` with the name ".pygfolder".


First run
=========

For the first run, `PyGFolder` must request a token to the API. It can be accomplished by invoking the `request_token()` method:


.. code:: python

    >>> from pygfolder import PyGFolder
    >>>
    >>> pygfolder = PyGFolder()
    >>> pygfolder.request_token()

This call will print a URL that you might need to visit in order to give access to `PyGFolder`. The step will finish when the code is retrieved back and manually filled into ".pygfolder".
An example of the file should be as follows:

.. code:: json
    
    {
        "installed": {
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "redirect_uris": [
                "urn:ietf:wg:oauth:2.0:oob",
                "http://localhost"
            ],
            "project_id": "vast-ascent-XXXXXX",
            "client_id": "XXXXXX.apps.googleusercontent.com",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "token_uri": "https://accounts.google.com/o/oauth2/token",
            "code": "THE_CODE_RETURNED_BY_GOOGLE_MANUALLY_SET_HERE",
            "client_secret": "XXXXXX"
        }
    }

Once the code is filled, `PyGFolder` will read it automatically (it has a trigger), and request an authorization token, which will be saved in the same file.
Next executions of `PyGFolder` will not require this process, thus it should be only run once per machine.

Note that "~/.pygfolder" contains all the required credentials data for `PyGFolder` to run. This means that transfering this file into another computer will allow `PyGFolder` to work out-of-the-box.


USAGE
=====

* **List elements in google drive:**

.. code:: python

    >>> from pygfolder import PyGFolder
    >>>
    >>> pygfolder = PyGFolder("")
    >>> print(pygfolder.keys())     # show files and folders
    >>> print(pygfolder.files())    # show only files
    >>> print(pygfolder.folders())  # show only folders

* **Create a file with a specific content:**

.. code:: python

    >>> pygfolder['pygfolder_file.txt'] = b"Hello, this is the content of this root file from now on"

* **Access an element:**

.. code:: python

    >>> file_content = pygfolder['pygfolder_file.txt']  # For accessing a file content
    >>> file_content = pygfolder['specific_folder']     # For accessing a folder content

In `PyGFolder`, each folder is represented by a `PyGFolder` object. For this reason, it is possible to access nested folders as follows:

.. code:: python

    >>> folder = pygfolder['specific_folder1']['specific_folder2'] 
    >>> folder = pygfolder['specific_folder1/specific_folder2']  # This is also equivalent


* **Delete an element:**

.. code:: python

    >>> del pygfolder['pygfolder_file.txt'])   

* **Iterate over files:**

.. code:: python

    >>> for file, content in pygfolder.items()):
    >>>     print(content)


* **Export documents:**

Google Apps stores the created documents within Google Drive, but they are not directly downloadable. If you want to download any of these, it must be exported to a specific `MimeType`.

.. code:: python

    >>> result = pygfolder.export('My presentation', mimetype="application/pdf")   

* **Create a folder:**

Folders are automatically handled by `PyGFolder`. An example that is going to force `PyGFolder` to create a folder is as follows:

.. code:: python

    >>> result = pygfolder["folder/content.txt"] = b"this will create automatically the folder 'folder' in order to create the file 'content.txt'"


LICENSE
=======

It is released under the *MIT license*.
