import pytest

from utils.factories import *

@pytest.fixture
def team():
    return TeamFactory()

