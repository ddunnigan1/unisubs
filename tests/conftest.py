from __future__ import absolute_import

import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
import django.test.client
import django.utils.encoding
from django_redis import get_redis_connection
import py.path
import pytest

from amara.signals import before_tests
from auth.models import CustomUser
from utils.test_utils import monkeypatch

patcher = None

def pytest_configure(config):
    global patcher
    patcher = monkeypatch.MonkeyPatcher()
    patcher.patch_functions()
    patch_mockredis()

    settings.MEDIA_ROOT = tempfile.mkdtemp(prefix='amara-test-media-root')

    reporter = config.pluginmanager.getplugin('terminalreporter')
    reporter.startdir = py.path.local('/run/pytest/')

    before_tests.send(config)

def patch_mockredis():
    from mockredis.client import MockRedis
    # Patch for mockredis returning a boolean when it should return 1 or 0.
    # (See https://github.com/locationlabs/mockredis/issues/147)
    def exists(self, key):
        if self._encode(key) in self.redis:
            return 1
        else:
            return 0
    MockRedis.exists = exists

    # Emulate PERSIST
    def persist(self, key):
        key = self._encode(key)
        if key in self.redis and key in self.timeouts:
            del self.timeouts[key]
            return 1
        else:
            return 0
    MockRedis.persist = persist

def pytest_unconfigure(config):
    patcher.unpatch_functions()
    shutil.rmtree(settings.MEDIA_ROOT)

def pytest_runtest_teardown(item, nextitem):
    from django_redis import get_redis_connection
    patcher.reset_mocks()
    get_redis_connection("default").flushdb()

@pytest.fixture(autouse=True)
def setup_amara_db(db):
    CustomUser.get_amara_anonymous()

@pytest.fixture
def redis_connection():
    return get_redis_connection('default')
