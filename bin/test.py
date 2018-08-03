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
    setup_test_links(optionalapps.project_root, testdir)
    for repo_path in optionalapps.get_repository_paths():
        setup_test_links(repo_path, testdir)

def setup_test_links(repo_path, testdir):
    source_test_dir = os.path.join(repo_path, testdir)
    if not os.path.exists(source_test_dir):
        return
    for filename in os.listdir(source_test_dir):
        if filename.endswith('.pyc'):
            continue
        src_path = os.path.join(source_test_dir, filename)
        dest_path = os.path.join(filename)
        try:
            os.symlink(src_path, dest_path)
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
