from textwrap import dedent


class InvalidRequest(Exception):
    def __init__(self, msg):
        self.msg = msg


def handle_error(ex):
    return (
        dedent(
            f"""\
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
        <title>{ex.code} {ex.name}</title>
        <h1>{ex.name}</h1>
        <p><img src="https://http.cat/{ex.code}"></img></p>
        """
        ),
        ex.code,
    )


def register_error_handlers(app):
    # TODO: register this for all status codes (iterate over a list of them)
    app.register_error_handler(404, handle_error)
    app.register_error_handler(405, handle_error)
    app.register_error_handler(500, handle_error)
