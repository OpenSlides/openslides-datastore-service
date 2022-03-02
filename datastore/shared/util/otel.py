import os
from contextlib import nullcontext

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from datastore.shared.di import injector
from datastore.shared.services import EnvironmentService


"""
Initializes the opentelemetry components and connection to the otel collector.
"""
def init(service_name):
    env_service = injector.get(EnvironmentService)
    if not env_service.is_otel_enabled():
        return

    span_exporter = OTLPSpanExporter(
        endpoint=f"http://collector:4317",
        insecure=True
        # optional
        # credentials=ChannelCredentials(credentials),
        # headers=(("metadata", "metadata")),
    )
    tracer_provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: service_name})
    )
    trace.set_tracer_provider(tracer_provider)
    span_processor = BatchSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)

def instrument_flask(app):
    FlaskInstrumentor().instrument_app(app)

"""
Returns a new child span to the currently active span.
If OPENTELEMETRY_ENABLED is not truthy a nullcontext will be returned instead.
So at any point in the code this function can be called in a with statement
without any additional checking needed.

Example:
```
with make_span("foo") as span:
    ...
    with make_span("bar", { "key": "value", ... }) as subspan:
        ...
```
"""
def make_span(name, attributes=None):
    env_service = injector.get(EnvironmentService)
    if not env_service.is_otel_enabled():
        return nullcontext()

    tracer = trace.get_tracer(__name__)
    span = tracer.start_as_current_span(name)
    if attributes is not None:
        span.set_attributes(attributes)

    return span
