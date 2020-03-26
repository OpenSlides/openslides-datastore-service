from reader.flask_frontend.flask_frontend import URL_PREFIX
from reader.flask_frontend.routes import Route
from shared.flask_frontend import unify_urls


GET_URL = unify_urls(URL_PREFIX, Route.GET.value)
