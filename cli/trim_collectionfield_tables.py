import sys
from datetime import datetime, timedelta
from textwrap import dedent

from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.writer.app import register_services


def main(args: list[str] = []):
    """
    Usage: python trim_collectionfield_tables.py [days=1]
    Trims all collectionfield tables by deleting all entries which are older than the given amount
    of days (which may be a floating point number).
    """
    register_services()
    connection: ConnectionHandler = injector.get(ConnectionHandler)

    delta = float(args[1]) if len(args) > 1 else 1
    threshold = datetime.now() - timedelta(days=delta)
    with connection.get_connection_context():
        # delete collectionsfields which haven't been updated in the last 24 hours
        connection.execute(
            dedent(
                """\
                DELETE FROM collectionfields cf
                    USING positions p
                WHERE cf.position = p.position AND p.timestamp < %s
                """
            ),
            [threshold],
        )
        # delete events_to_collectionfields from events older than 24 hours
        connection.execute(
            dedent(
                """\
                DELETE FROM events_to_collectionfields ecf
                    USING events e, positions p
                WHERE ecf.event_id = e.id AND e.position = p.position AND p.timestamp < %s
                """
            ),
            [threshold],
        )


if __name__ == "__main__":
    sys.exit(main(sys.argv))
