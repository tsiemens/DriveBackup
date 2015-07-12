# DriveBackup
A python library for backing up single data store files to Google Drive

DriveBackup uses Google's [skicka](https://github.com/google/skicka) command line tool to communicate with your Google Drive account.
You may ask 'why?'. The answer was that I didn't want to register a Google app just to use the api library.

## Use
This script is not available via pip. Copy the file into your project, or into .local/lib/python%d/site-packages
You will also need to copy bin/skicka-* to an executable called skicka in your PATH.

See example.py for a very simple example for getting started.

It is best used for managing a single file and backing it up into Google Drive, generally from a single client.
Versioning is simplistic, and requires manual resolve if conflicts are created.
