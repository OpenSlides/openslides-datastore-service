from datastore.reader.flask_frontend import FlaskFrontend
from datastore.reader.services import register_services
from datastore.shared import create_base_application


def create_application():
    register_services()
    return create_base_application(FlaskFrontend)


application = create_application()


from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)


span_exporter = OTLPSpanExporter(
    # optional
    endpoint="collector:4317",
    # credentials=ChannelCredentials(credentials),
    # headers=(("metadata", "metadata")),
)
tracer_provider = TracerProvider(
    resource=Resource.create({SERVICE_NAME: "datastore-reader"})
)
trace.set_tracer_provider(tracer_provider)
span_processor = BatchSpanProcessor(span_exporter)
tracer_provider.add_span_processor(span_processor)

FlaskInstrumentor().instrument_app(application)
