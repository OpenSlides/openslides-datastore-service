from . import core, flask_frontend  # noqa


def setup_di():
    from .core import setup_di as core_setup_di

    core_setup_di()
