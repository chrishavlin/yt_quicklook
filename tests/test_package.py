from __future__ import annotations

import importlib.metadata

import yt_quicklook as m


def test_version():
    assert importlib.metadata.version("yt_quicklook") == m.__version__
