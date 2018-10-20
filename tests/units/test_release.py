import pytest

from magnate import release


def test_release_info():
    assert hasattr(release, 'AUTHOR')
    assert hasattr(release, 'MAINTAINER')
    assert hasattr(release, 'PROGRAM_NAME')
    assert hasattr(release, 'COPYRIGHT_YEAR')
    assert hasattr(release, 'LICENSE')


def test_version_correct():
    assert '.'.join(release.__version_info__) == release.__version__
