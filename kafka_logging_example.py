"""
Example configuration for using KafkaLoggingHandler in Django settings.

This file shows how to integrate the KafkaLoggingHandler into your Django logging configuration.
You can copy the relevant parts into your settings.py file.
"""

# Example Django logging configuration with KafkaLoggingHandler
LOGGING_WITH_KAFKA = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        # Existing handlers (keep your current ones)
        'badgr_debug': {
            'level': 'DEBUG',
            'formatter': 'badgr',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'H',
            'interval': 1,
            'backupCount': 30 * 24,
            'filename': '/path/to/logs/badgr_debug.log',
        },
        
        # New Kafka handlers
        'kafka_debug': {
            'level': 'DEBUG',
            'class': 'mainsite.handlers.KafkaLoggingHandler',
            'topic': 'badgr-debug-logs',
            'bootstrap_servers': 'localhost:9092',
            # Optional additional Kafka producer settings
            'retries': 3,
            'acks': 1,
            'linger_ms': 100,
            'batch_size': 16384,
        },
        
        'kafka_events': {
            'level': 'INFO',
            'class': 'mainsite.handlers.AsyncKafkaLoggingHandler',
            'topic': 'badgr-events',
            'bootstrap_servers': 'localhost:9092',
            'buffer_size': 50,
            'flush_interval': 5.0,
            # Optional additional Kafka producer settings
            'retries': 3,
            'acks': 1,
        },
        
        'kafka_errors': {
            'level': 'ERROR',
            'class': 'mainsite.handlers.KafkaLoggingHandler',
            'topic': 'badgr-errors',
            'bootstrap_servers': 'localhost:9092',
        },
    },
    'loggers': {
        'Badgr.Debug': {
            'handlers': ['badgr_debug', 'kafka_debug'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'Badgr.Events': {
            'handlers': ['kafka_events'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['kafka_errors'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
    'formatters': {
        'badgr': {'format': '%(asctime)s | %(levelname)s | %(message)s'},
    },
}

# Environment variables you might want to set:
# KAFKA_BOOTSTRAP_SERVERS=localhost:9092
# KAFKA_DEBUG_TOPIC=badgr-debug-logs
# KAFKA_EVENTS_TOPIC=badgr-events
# KAFKA_ERRORS_TOPIC=badgr-errors

# Example usage in settings.py:
"""
import os

# Kafka configuration from environment
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_DEBUG_TOPIC = os.environ.get('KAFKA_DEBUG_TOPIC', 'badgr-debug-logs')
KAFKA_EVENTS_TOPIC = os.environ.get('KAFKA_EVENTS_TOPIC', 'badgr-events')
KAFKA_ERRORS_TOPIC = os.environ.get('KAFKA_ERRORS_TOPIC', 'badgr-errors')

# Add Kafka handlers to existing logging configuration
if 'kafka_debug' not in LOGGING['handlers']:
    LOGGING['handlers']['kafka_debug'] = {
        'level': 'DEBUG',
        'class': 'mainsite.handlers.AsyncKafkaLoggingHandler',
        'topic': KAFKA_DEBUG_TOPIC,
        'bootstrap_servers': KAFKA_BOOTSTRAP_SERVERS,
        'buffer_size': 100,
        'flush_interval': 5.0,
    }
    
    # Add to existing debug handlers
    if 'Badgr.Debug' in LOGGING['loggers']:
        LOGGING['loggers']['Badgr.Debug']['handlers'].append('kafka_debug')
"""