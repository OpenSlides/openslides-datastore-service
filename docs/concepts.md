# OpenSlides datastore service

## Basics

The datastore consists of a chain of _events_. An event captures a single modification of a single model, which may be the creation, an update, deletion or restoration. This is saved in the _event\_type_ (compare [the specs](https://github.com/OpenSlides/OpenSlides/blob/openslides4-dev/docs/interfaces/datastore-service.txt#L79)).

Apart from the information about the event itself (e.g. the updated fields), every event is assigned a _position_. Every call to the `write` method generates a new position. Multiple events can share the same position if they are send in the same request. You can think of the position as a kind of "transaction number", except that there is no actual transaction happening. Instead, the datastore follows an optimistic concurrency control (OCC) pattern.

## Optimistic concurrency control

Since in OpenSlides we do not have many concurrent write requests, the datastore does not lock models or even whole collections and does not have a classical transaction model. Instead, with every call to one of the reader's methods the current position of the datastore is returned (meaning the global maximum of all positions). If locking of fields, models or collections is needed, this always happens after some data has been requested from the datastore<sup> [citation needed]</sup>, so the returned position can be send as a locking indicator in the write request.

### Locking

In every write request, the `locked_fields` parameter can be given to indicate what to lock and on which position the underlying information was acquired. Suppose I want to fetch the model `c/1` from the datastore, update its value based on the current value and then write it back. The `get` response could look like this:

    {
        // ...
        "value": 100,
        "meta_position": 42,
        // ...
    }
   
I want to add 100 to `value` and then write it back to the datastore. After building the rest of the update event, I can add the following:

    {
        // ...
        "locked_fields": {
            "c/1/value": 42
        }
    }

where `42` is the position returned from the `get` request. If there was no event after the `get` request which modified the field `c/1/value`, this request can just be executed since the value must still be 100. If the value was modified in the meantime, the request is rejected with an `ModelLockedException` and has to be restarted by the client.

The keys of the `locked_fields` object can be fqfields, fqids or whole collections.

## Null values

To simplify communication, the datastore assumes `null === undefined`. This means that writing `null` to any field or model equals the deletion of it. As a consequence, the datastore will never return `null` values on any `read` request.

## PostgreSQL backend limitations

The current implementation of the datastore uses a PostgreSQL backend as its database. For better indexing purposes, the keys (collections, ids and fields) are stored with a fixed length instead of a variable one. The following maximum length restrictions apply when using the PostgreSQL backend:

    collection: 32
    id: 16
    field: 207

Longer keys will be rejected with an `InvalidFormat` error.