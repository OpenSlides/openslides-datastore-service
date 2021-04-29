from .init import init

init()

from .handler import handle_request  # noqa
from reader.flask_frontend.routes import Route  # noqa
