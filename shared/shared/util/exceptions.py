class DatastoreException(Exception):
    pass


class InvalidFormat(DatastoreException):
    def __init__(self, msg):
        self.msg = msg


class ModelDoesNotExist(DatastoreException):
    def __init__(self, fqid):
        self.fqid = fqid


class ModelExists(DatastoreException):
    def __init__(self, fqid):
        self.fqid = fqid


class ModelNotDeleted(DatastoreException):
    def __init__(self, fqid):
        self.fqid = fqid


class ModelLocked(DatastoreException):
    def __init__(self, key):
        self.key = key


class BadCodingError(RuntimeError):
    """
    Should be thrown for errors that theoretically should never happen, except when the
    programmer fucked up.
    """

    pass
