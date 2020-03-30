from reader.flask_frontend.flask_frontend import URL_PREFIX
from reader.flask_frontend.routes import Route
from shared.flask_frontend import unify_urls


for route in Route:
    globals()[route.upper() + "_URL"] = unify_urls(URL_PREFIX, route)
