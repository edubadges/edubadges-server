#!/usr/bin/env python3
"""
Test script for KafkaLoggingHandler

This script tests the KafkaLoggingHandler without requiring a real Kafka instance.
It uses mocks to simulate Kafka behavior and verify the handler works correctly.
"""

import logging
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))

def test_kafka_handler_import():
    """Test that the handler can be imported correctly."""
    print("Testing KafkaLoggingHandler import...")
    
    try:
        from mainsite.handlers import KafkaLoggingHandler, AsyncKafkaLoggingHandler
        print("✓ Successfully imported KafkaLoggingHandler and AsyncKafkaLoggingHandler")
        return True
    except Exception as e:
        print(f"✗ Failed to import handlers: {e}")
        return False


def test_kafka_handler_without_kafka():
    """Test handler behavior when kafka-python is not available."""
    print("\nTesting KafkaLoggingHandler without kafka-python...")
    
    # Mock the kafka import to simulate it not being available
    with patch.dict('sys.modules', {'kafka': None, 'kafka.errors': None}):
        try:
            from mainsite.handlers import KafkaLoggingHandler
            
            # This should raise ImportError since kafka is not available
            try:
                handler = KafkaLoggingHandler("test-topic")
                print("✗ Expected ImportError when kafka-python not available")
                return False
            except ImportError as e:
                print(f"✓ Correctly raised ImportError: {e}")
                return True
                
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return False


def test_kafka_handler_with_mock_kafka():
    """Test handler with mocked Kafka producer."""
    print("\nTesting KafkaLoggingHandler with mocked Kafka...")
    
    try:
        # Mock the kafka module at import time
        kafka_mock = Mock()
        producer_mock = Mock()
        future_mock = Mock()
        
        kafka_mock.KafkaProducer = Mock(return_value=producer_mock)
        kafka_mock.errors = Mock()
        kafka_mock.errors.KafkaError = Exception
        producer_mock.send.return_value = future_mock
        
        with patch.dict('sys.modules', {'kafka': kafka_mock, 'kafka.errors': kafka_mock.errors}):
            from mainsite.handlers import KafkaLoggingHandler
            
            # Create handler
            handler = KafkaLoggingHandler("test-topic", bootstrap_servers="localhost:9092")
            
            # Create a test logger
            logger = logging.getLogger('test_logger')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)
            
            # Test logging
            logger.info("Test message")
            logger.warning("Warning message", extra={'user_id': 123})
            
            try:
                raise ValueError("Test exception")
            except ValueError:
                logger.exception("Exception occurred")
            
            # Verify producer.send was called
            assert producer_mock.send.called, "Producer send method should be called"
            print(f"✓ Producer send called {producer_mock.send.call_count} times")
            
            # Check the calls
            calls = producer_mock.send.call_args_list
            for i, call in enumerate(calls):
                args, kwargs = call
                print(f"  Call {i+1}: topic={kwargs.get('topic')}, key={kwargs.get('key')}")
                
                # Verify message structure
                message = kwargs.get('value')
                if message:
                    assert 'timestamp' in message
                    assert 'level' in message
                    assert 'message' in message
                    assert 'logger_name' in message
                    print(f"    Message: {message['level']} - {message['message']}")
            
            # Test handler close
            handler.close()
            producer_mock.close.assert_called_once()
            print("✓ Handler closed successfully")
            
            return True
            
    except Exception as e:
        print(f"✗ Error testing handler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_async_kafka_handler():
    """Test the async version of the Kafka handler."""
    print("\nTesting AsyncKafkaLoggingHandler...")
    
    try:
        # Mock the kafka module at import time
        kafka_mock = Mock()
        producer_mock = Mock()
        future_mock = Mock()
        
        kafka_mock.KafkaProducer = Mock(return_value=producer_mock)
        kafka_mock.errors = Mock()
        kafka_mock.errors.KafkaError = Exception
        producer_mock.send.return_value = future_mock
        
        with patch.dict('sys.modules', {'kafka': kafka_mock, 'kafka.errors': kafka_mock.errors}):
            from mainsite.handlers import AsyncKafkaLoggingHandler
            
            # Create async handler with small buffer for testing
            handler = AsyncKafkaLoggingHandler(
                "test-topic", 
                bootstrap_servers="localhost:9092",
                buffer_size=2,
                flush_interval=10.0  # Long interval to avoid time-based flushing in test
            )
            
            # Create a test logger
            logger = logging.getLogger('async_test_logger')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)
            
            # Test buffered logging
            logger.info("Message 1")
            
            # Should not have sent yet (buffer size is 2)
            assert not producer_mock.send.called, "Should not send before buffer is full"
            
            logger.info("Message 2")
            
            # Should have sent now (buffer is full)
            assert producer_mock.send.called, "Should send when buffer is full"
            print(f"✓ Buffered messages sent after reaching buffer size")
            
            # Test manual flush
            producer_mock.send.reset_mock()
            logger.info("Message 3")
            handler.flush()
            
            assert producer_mock.send.called, "Should send when manually flushed"
            print("✓ Manual flush works correctly")
            
            handler.close()
            return True
            
    except Exception as e:
        print(f"✗ Error testing async handler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_format():
    """Test the log message format."""
    print("\nTesting log message format...")
    
    try:
        # Mock the kafka module at import time
        kafka_mock = Mock()
        producer_mock = Mock()
        future_mock = Mock()
        
        kafka_mock.KafkaProducer = Mock(return_value=producer_mock)
        kafka_mock.errors = Mock()
        kafka_mock.errors.KafkaError = Exception
        producer_mock.send.return_value = future_mock
        
        with patch.dict('sys.modules', {'kafka': kafka_mock, 'kafka.errors': kafka_mock.errors}):
            from mainsite.handlers import KafkaLoggingHandler
            
            handler = KafkaLoggingHandler("test-topic")
            
            # Create a log record
            record = logging.LogRecord(
                name='test.logger',
                level=logging.INFO,
                pathname='/path/to/file.py',
                lineno=42,
                msg='Test message with %s',
                args=('argument',),
                exc_info=None
            )
            
            # Format the record
            formatted = handler.format_record(record)
            
            # Check required fields
            required_fields = [
                'timestamp', 'level', 'logger_name', 'message',
                'module', 'filename', 'line_number', 'function_name',
                'process_id', 'thread_id'
            ]
            
            for field in required_fields:
                assert field in formatted, f"Missing required field: {field}"
            
            assert formatted['level'] == 'INFO'
            assert formatted['logger_name'] == 'test.logger'
            assert formatted['message'] == 'Test message with argument'
            assert formatted['line_number'] == 42
            
            print("✓ Message format contains all required fields")
            
            # Test with extra attributes
            record.user_id = 123
            record.request_id = 'abc-123'
            
            formatted = handler.format_record(record)
            assert 'extra' in formatted
            assert formatted['extra']['user_id'] == 123
            assert formatted['extra']['request_id'] == 'abc-123'
            
            print("✓ Extra attributes included correctly")
            
            return True
            
    except Exception as e:
        print(f"✗ Error testing message format: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("Testing KafkaLoggingHandler Implementation")
    print("=" * 50)
    
    tests = [
        test_kafka_handler_import,
        test_kafka_handler_without_kafka,
        test_kafka_handler_with_mock_kafka,
        test_async_kafka_handler,
        test_message_format,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())