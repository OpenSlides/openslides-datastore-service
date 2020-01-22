class WriterException(Exception):
    pass


class InvalidFormat(WriterException):
    def __init__(self, msg):
        self.msg = msg


class ModelDoesNotExist(WriterException):
    def __init__(self, fqid):
        self.fqid = fqid


class ModelExists(WriterException):
    def __init__(self, fqid):
        self.fqid = fqid


class ModelNotDeleted(WriterException):
    def __init__(self, fqid):
        self.fqid = fqid


class ModelLocked(WriterException):
    def __init__(self, key):
        self.key = key
