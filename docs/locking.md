# Locking

Some nomenclature:
* A *lock* is a position which is provided together with either a FQID, a FQField or a
  CollectionField.
* A lock is *broken* if an update occured to the given identifier which may invalidate the data
  which was read together with the lock.

## FullQualifiedIds

This is the easiest case: All FQIDs are mapped to the positions where they are modified by the
`events` table. So we only have to check if an event for this FQID exists with a position greater
than the lock to see if the lock was broken. 

## CollectionFields

Since we have no easy way to determine which events modify which fields except filtering by the
prefix of the FQID and the content of the JSON data (which would be very impracticle), we introduced
an extra table `collectionfields`, which saves for each collectionfield the highest position in the
datastore. This table is automatically updated on every event execution according to the contents of
the event.

The size of this table is neglectable since we have at most one row per field in the models
definition (see https://github.com/OpenSlides/openslides-meta/models.yml),
which is currently a little over 2000 lines long. Since most field definitions are multiline, this
is a very high upper limit for the number of fields, but even 2000 entries in the table is nothing
in comparison to the `events` table.

With the help of this table, the lock check becomes as easy as the one above, since we only need to
check if the position for the given collectionfield is higher than the lock.

### CollectionFields with filter

This feature is useful e.g. for `FILTER` requests. Normally, if a filter is done on a
collectionfield `a/b`, the whole collectionfield would have to be locked for the filter to still be
valid after another action changes some of it. By appending the used filter to the lock, it can be
checked if some content inside the filter scope changed, so there can potentially be more changes in
parallel on the same collectionfield.

## FullQualifiedFields

To check FQField locks, the above methods have to be combined: We first filter the events for all
matching ones with the FQID of the FQField and a position greater than the lock. Then, we join the
`collectionfield` table with the events and filter for the field part of the FQField. This requires
2 queries in total (one "normal" and a subquery), but should still be performant enough.
