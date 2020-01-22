from .dependency_provider import (  # noqa
    injector,
    service_as_factory,
    service_as_singleton,
    service_interface,
)


"""
def inject(*protocols):
    def wrapper(init):
        arg_names = inspect.getfullargspec(init)[0]

        def new_init(self, *args, **kwargs):
            services = map(lambda protocol: injector.get(protocol), protocols)
            mapping = {x[0]: x[1] for x in zip(arg_names[1:], services)}
            init(self, **mapping)

        return new_init

    return wrapper
"""
