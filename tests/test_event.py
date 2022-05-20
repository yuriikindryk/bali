import os

import amqp
import pytest
from kombu import Connection, Queue, Exchange

from bali.core import _settings
from bali.decorators import event_handler
from bali.events import Event, dispatch, handle

_settings.AMQP_CONFIGS  = {
    'default':
        {
            'AMQP_SERVER_ADDRESS':
                os.getenv(
                    'AMQP_SERVER_ADDRESS', default='amqp://127.0.0.1:5672'
                ),
            'EXCHANGE_NAME':
                'HELLO_WORLD_TEST',
            'EXCHANGE_TYPE': 'fanout',
            'QUEUE_NAME':
                'QUEQUE_C'
        }
}
_settings.EVENT_TYPE_TO_AMQP = {'test0': 'default', 'test1': 'default'}


@event_handler(event_type='test0')
def call_test0(event):
    print('test0 received:', event)
    print(os.path.dirname('bbb.txt'))


@event_handler(event_type='test1')
def call_test1(event):
    print('test1 received:', event)
    print(os.path.basename('aaa.txt'))


def test_event_dispatch():
    _settings.AMQP_CONFIGS = {
        'default':
            {
                'AMQP_SERVER_ADDRESS':
                    os.getenv(
                        'AMQP_SERVER_ADDRESS', default='amqp://127.0.0.1:5672'
                    ),
                'EXCHANGE_NAME':
                    'HELLO_WORLD_TEST',
                'EXCHANGE_TYPE':
                    'fanout'
            }
    }
    _settings.EVENT_TYPE_TO_AMQP = {'test0': 'default', 'test1': 'default'}
    for i in range(100):
        event = Event(type='test0', payload={'hello': 'world2222222'})
        assert dispatch(event)
    for i in range(100):
        event = Event(type='test1', payload={'hello': 'world1111111'})
        assert dispatch(event)


handle()


def test_event_handler(mocker):
    mocker.patch('os.path.basename')
    mocker.patch('os.path.dirname')
    handle()
    os.path.basename.assert_called_with('aaa.txt')
    os.path.dirname.assert_called_with('bbb.txt')


def test_queue_declared_in_event_handler(mocker):
    # 1. Define a `Product` service
    service_abbr = 'product'
    uri = os.getenv('AMQP_SERVER_ADDRESS', default='amqp://127.0.0.1:5672')
    _settings.AMQP_CONFIGS = {
        'default': {
            'AMQP_SERVER_ADDRESS': uri,
            'EXCHANGE_NAME': 'ms.events',
            'EXCHANGE_TYPE': 'fanout',
            'QUEUE_NAME': f'{service_abbr}.events',
        }
    }
    # 2. Ensure RabbitMQ has no queue for `Product` service
    amqp_server_address = 'amqp://127.0.0.1:5672'
    conn = Connection(amqp_server_address)
    channel = conn.channel()
    exchange = Exchange('ms.events', type='fanout')
    queue_name = f'{service_abbr}.events'

    b = Queue(queue_name, exchange, queue_name, channel=channel)
    with pytest.raises(amqp.exceptions.NotFound):
        b.queue_declare(passive=True)

    # 3. Launch `Product` service's handle
    from bali.decorators import event_handler

    @event_handler('UserCreated')
    def handle_product_created(event):
        pass

    handle()
    # 4. Assert `product.events` queue exists，and bind to exchange `ms.events`
    b = Queue(queue_name, exchange, queue_name, channel=channel)
    assert b.queue_declare(passive=True)
    # assert 'exchange_declare' in channel
    # assert 'queue_declare' in channel
    # assert 'queue_bind' in channel

    # clean
    conn.close()
