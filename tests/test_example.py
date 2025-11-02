"""Example tests for plumbum."""

from pdum import plumbum


def test_version():
    """Test that the package has a version."""
    assert hasattr(plumbum, "__version__")
    assert isinstance(plumbum.__version__, str)
    assert len(plumbum.__version__) > 0


def test_import():
    """Test that the package can be imported."""
    assert plumbum is not None
