from __future__ import absolute_import

import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
import django.test.client
import django.utils.encoding
import py.path
import pytest

from amara.signals import before_tests
from auth.models import CustomUser
from utils.test_utils import monkeypatch, restframeworkcompat

patcher = None

def pytest_configure(config):
    global patcher
    patcher = monkeypatch.MonkeyPatcher()
    patcher.patch_functions()
    patch_for_rest_framework()

    settings.MEDIA_ROOT = tempfile.mkdtemp(prefix='amara-test-media-root')

    reporter = config.pluginmanager.getplugin('terminalreporter')
    reporter.startdir = py.path.local('/run/pytest/')

    before_tests.send(config)

def patch_for_rest_framework():
    # patch some of old django code to be compatible with the rest
    # framework testing tools
    # restframeworkcompat is the compat module from django-rest-framework
    # 3.0.3
    django.test.client.RequestFactory = restframeworkcompat.RequestFactory
    django.utils.encoding.force_bytes = restframeworkcompat.force_bytes_or_smart_bytes

def pytest_unconfigure(config):
    patcher.unpatch_functions()
    shutil.rmtree(settings.MEDIA_ROOT)

def pytest_runtest_teardown(item, nextitem):
    patcher.reset_mocks()
    cache.clear()

@pytest.fixture(autouse=True)
def setup_amara_db(db):
    CustomUser.get_amara_anonymous()
