import pytest

from tests.helpers import create_default_test_order, silent_storage_reset


@pytest.fixture
def clean_storage():
    silent_storage_reset()
    yield
    silent_storage_reset()
