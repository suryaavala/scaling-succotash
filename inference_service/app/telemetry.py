"""OpenTelemetry configuration module for Inference operations."""
import logging
import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger("telemetry")

def setup_telemetry(app: FastAPI, service_name: str) -> None:
    """Configures Jaeger and OTEL propagation hooks."""
    jaeger_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    resource = Resource.create(attributes={"service.name": service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        
        FastAPIInstrumentor.instrument_app(app)
        logger.info(f"OpenTelemetry instrumented for {service_name}")
    except Exception as e:
        logger.error(f"Failed to setup telemetry: {e}")
