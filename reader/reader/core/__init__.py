from .reader import Reader


def setup_di():
    from shared.di import injector

    from .reader_service import ReaderService

    injector.register(Reader, ReaderService)
