import json
import logging
import time
import datetime
import traceback
from typing import Dict, Any, Optional

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


class KafkaLoggingHandler(logging.Handler):
    """
    A logging handler that sends log messages to a Kafka topic.
    
    This handler sends log records to a specified Kafka topic. It requires
    the kafka-python library to be installed.
    
    Args:
        topic (str): The Kafka topic name to send logs to
        bootstrap_servers (list or str): Kafka bootstrap servers
        **kwargs: Additional KafkaProducer configuration options
    """
    
    def __init__(self, topic: str, bootstrap_servers: str = 'localhost:9092', **kwargs):
        super().__init__()
        
        # Check if kafka is available at runtime, not just at module import
        try:
            from kafka import KafkaProducer
            from kafka.errors import KafkaError
        except ImportError:
            raise ImportError(
                "kafka-python library is required for KafkaLoggingHandler. "
                "Install with: pip install kafka-python"
            )
        
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        
        # Default producer configuration
        producer_config = {
            'bootstrap_servers': bootstrap_servers,
            'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
            'key_serializer': lambda k: k.encode('utf-8') if k else None,
            'retries': 3,
            'acks': 1,
            'linger_ms': 100,
            'batch_size': 16384,
        }
        
        # Override with any additional kwargs
        producer_config.update(kwargs)
        
        try:
            self.producer = KafkaProducer(**producer_config)
        except Exception as e:
            # If we can't connect to Kafka, we should fail gracefully
            self.producer = None
            self.handleError(logging.LogRecord(
                name='KafkaLoggingHandler',
                level=logging.ERROR,
                pathname='',
                lineno=0,
                msg=f"Failed to initialize Kafka producer: {e}",
                args=(),
                exc_info=None
            ))
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to Kafka.
        
        Args:
            record: The LogRecord to emit
        """
        if not self.producer:
            return
        
        try:
            # Format the log record
            log_message = self.format_record(record)
            
            # Send to Kafka with the logger name as the key for partitioning
            future = self.producer.send(
                topic=self.topic,
                value=log_message,
                key=record.name
            )
            
            # We can optionally wait for confirmation, but for performance
            # we'll send asynchronously and handle errors in the callback
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
            
        except Exception as e:
            self.handleError(record)
    
    def format_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Format a log record into a dictionary suitable for JSON serialization.
        
        Args:
            record: The LogRecord to format
            
        Returns:
            Dictionary containing the log record data
        """
        # Start with the formatted message
        message = {
            'timestamp': datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc).isoformat(),
            'level': record.levelname,
            'logger_name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'filename': record.filename,
            'line_number': record.lineno,
            'function_name': record.funcName,
            'process_id': record.process,
            'thread_id': record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            message['exception'] = ''.join(traceback.format_exception(*record.exc_info))
        
        # Add any extra attributes that were passed to the log call
        extra_attributes = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'message'
            }:
                try:
                    # Only include JSON-serializable values
                    json.dumps(value)
                    extra_attributes[key] = value
                except (TypeError, ValueError):
                    # Skip non-serializable values
                    pass
        
        if extra_attributes:
            message['extra'] = extra_attributes
        
        return message
    
    def _on_send_success(self, record_metadata):
        """Callback for successful Kafka send."""
        # Could add metrics/monitoring here if needed
        pass
    
    def _on_send_error(self, exception):
        """Callback for failed Kafka send."""
        # Log the error using the standard logging system
        # to avoid infinite recursion
        print(f"Failed to send log to Kafka: {exception}")
    
    def flush(self) -> None:
        """Flush any pending log records."""
        if self.producer:
            try:
                self.producer.flush()
            except Exception as e:
                # Handle flush errors gracefully
                print(f"Error flushing Kafka producer: {e}")
    
    def close(self) -> None:
        """Close the handler and clean up resources."""
        if self.producer:
            try:
                self.producer.close()
            except Exception as e:
                print(f"Error closing Kafka producer: {e}")
            finally:
                self.producer = None
        
        super().close()


class AsyncKafkaLoggingHandler(KafkaLoggingHandler):
    """
    An asynchronous version of KafkaLoggingHandler that buffers log messages
    and sends them in batches for better performance.
    """
    
    def __init__(self, topic: str, bootstrap_servers: str = 'localhost:9092', 
                 buffer_size: int = 100, flush_interval: float = 5.0, **kwargs):
        """
        Initialize the async Kafka logging handler.
        
        Args:
            topic: Kafka topic name
            bootstrap_servers: Kafka bootstrap servers
            buffer_size: Number of messages to buffer before auto-flushing
            flush_interval: Time in seconds between auto-flushes
            **kwargs: Additional KafkaProducer configuration
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self._buffer = []
        self._last_flush = time.time()  # Initialize to current time
        
        super().__init__(topic, bootstrap_servers, **kwargs)
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Buffer the log record and send when buffer is full or flush interval elapsed.
        """
        if not self.producer:
            return
        
        try:
            log_message = self.format_record(record)
            self._buffer.append((log_message, record.name))
            
            current_time = time.time()
            
            # Flush if buffer is full or enough time has passed
            if (len(self._buffer) >= self.buffer_size or 
                current_time - self._last_flush >= self.flush_interval):
                self._flush_buffer()
                self._last_flush = current_time
                
        except Exception as e:
            self.handleError(record)
    
    def _flush_buffer(self) -> None:
        """Send all buffered messages to Kafka."""
        if not self._buffer:
            return
        
        for message, key in self._buffer:
            try:
                future = self.producer.send(
                    topic=self.topic,
                    value=message,
                    key=key
                )
                future.add_errback(self._on_send_error)
            except Exception as e:
                self._on_send_error(e)
        
        self._buffer.clear()
    
    def flush(self) -> None:
        """Flush buffered messages and the Kafka producer."""
        self._flush_buffer()
        super().flush()