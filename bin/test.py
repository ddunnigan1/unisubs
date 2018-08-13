#!/usr/bin/python

"""
Amara testing script

Some notes about testing:

  - Before running this cd to a directory to put tests in.  The user running
    the script needs to be able to write to it.  In our docker file, we use
    /var/run/tests.

  - Pass as the first argument the directory that holds the test code (either
    "tests", or "guitests").

  - The test directory will be cleared out, then we will symlink all files
    found in the the tests/guitests directories (both from the unisubs repo,
    and any submodules)

"""

from __future__ import absolute_import
import os
import sys

import pytest

import optionalapps
import startup

def setup_test_directories(testdir):
    """
    Merge together the various test/ directories

    We allow each subrepository to create its own test directory, which then get
    merged together to create a virtual test package with some magic from
    tests/__init__.py.  However, this doesn't work with py.test, since it
    expects to be able to walk through the filesystem paths to find files like
    conftest.py.  To work around this, symlink all the actual files into an
    actual directory
    """
    setup_test_links(optionalapps.project_root, testdir)
    for repo_path in optionalapps.get_repository_paths():
        setup_test_links(repo_path, testdir)
    # create the __init__.py file
    with open('__init__.py', 'w'):
        pass
    # We now have a bunch of potential packages named "tests".  Mess with the
    # path/module registry to ensure that it's the one we just created the
    # symlinks with.
    sys.path.insert(0, '')
    import tests

def setup_test_links(repo_path, testdir):
    source_test_dir = os.path.join(repo_path, testdir)
    if not os.path.exists(source_test_dir):
        return
    for filename in os.listdir(source_test_dir):
        if filename.endswith('.pyc'):
            continue
        if filename == '__init__.py':
            # Don't copy the __init__.py files.  For one thing, there's
            # multiple of them.  For another, we don't want the code inside
            # them that messes with the python path
            continue
        src_path = os.path.join(source_test_dir, filename)
        try:
            os.symlink(src_path, filename)
        except OSError:
            print 'Error symlinking {}.  Is it duplicated?'.format(src_path)
            sys.exit(1)

def no_tests_specified(args):
    return all(arg.startswith('-') for arg in args[1:])

if __name__ == '__main__':
    startup.startup()
    # The first arg is the test directory to run.  Use that for
    # setup_test_directories, then remove it from the command line that pytest
    # sees
    testdir = sys.argv[1]
    setup_test_directories(testdir)
    pytest_args = sys.argv[0:1] + sys.argv[2:]
    if no_tests_specified(pytest_args):
        if testdir == 'tests':
            pytest_args.extend(['.', 'babelsubs.tests', 'unilangs.tests'])
        else:
            pytest_args.extend(['.'])
    sys.exit(pytest.main(pytest_args))
