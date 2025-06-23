import pika
from flask import g


def create_rabbitmq_connection():
    """
    Create a RabbitMQ connection using pika.
    """
    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('rabbitmq', 5672, '/', credentials)
    )
    channel = connection.channel()
    return connection, channel

def get_general_queue_name(queue_type, token):
    if token is None:
        from flask import g
        token = g.token
    return f"Queue Service:{queue_type} --- User: {token}"

def get_leakybucket_queue_name():
    user_token = getattr(g, 'token', 'anonymous')
    if user_token is None:
        user_token = 'anonymous'
    return get_general_queue_name("leaky_bucket", user_token)