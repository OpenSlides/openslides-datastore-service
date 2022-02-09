import os
from contextlib import nullcontext

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def init(service_name):
    if not is_truthy(os.environ.get("OPENTELEMETRY_ENABLED", "false")):
        return

    collector_host = os.environ.get("OPENTELEMETRY_COLLECTOR_HOST", "collector")
    collector_port = os.environ.get("OPENTELEMETRY_COLLECTOR_PORT", "4317")
    span_exporter = OTLPSpanExporter(
        endpoint=f"http://{collector_host}:{collector_port}",
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

def make_span(name):
    if not is_truthy(os.environ.get("OPENTELEMETRY_ENABLED", "false")):
        return nullcontext()

    tracer = trace.get_tracer(__name__)
    return tracer.start_as_current_span(name)

def is_truthy(value: str) -> bool:
    truthy = ("1", "on", "true")
    falsy = ("0", "off", "false")
    if value.lower() not in truthy + falsy:
        raise ValueError(f"Value must be one off {truthy + falsy}.")
    return value.lower() in truthy
