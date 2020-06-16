from shared.flask_frontend import unify_urls


URL_PREFIX = "/internal/datastore/writer/"


WRITE_URL = unify_urls(URL_PREFIX, "/write")
RESERVE_IDS_URL = unify_urls(URL_PREFIX, "/reserve_ids")
TRUNCATE_DB_URL = unify_urls(URL_PREFIX, "/truncate_db")
