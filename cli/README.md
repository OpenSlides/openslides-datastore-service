# CLI

The scripts in this folder must be executed from inside the container after the stack has been
started. Most of them are useful for developing and testing with the datastore. The script
`export_to_os3.py` can be used to export an existing OS4 meeting into the OS3 format as an SQL
script. The script `healthcheck.py` can be used to programmatically call the health route of the
current module.

## Trim collectionfield tables

The script `trim_collectionfields.py` can be used to remove outdated entries from the two
collectionfield helper tables to improve performance. This is best used in regular intervals, e.g.,
via a cronjob. It can be safely executed during production without shutting down any services as
long as the time span is long enough (longer than any running backend process, e.g., import may take).
