from typing import List, Union

class WriteRequest:
    def __init__(self, events: List[Union[CreateRequestEvent, RestoreRequestEvent, UpdateRequestEvent, DeleteRequestEvent]], information: Information
