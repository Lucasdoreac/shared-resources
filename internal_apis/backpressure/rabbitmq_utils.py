import os
import pika
from flask import g
from flask import request


# Defaults do bucket global quando GLOBAL_* não está definida (API e worker leem daqui).
GLOBAL_BUCKET_SIZE_DEFAULT = 100
GLOBAL_LEAK_RATE_DEFAULT = 0.1


def get_global_bucket_size():
    return int(os.getenv("GLOBAL_BUCKET_SIZE") or GLOBAL_BUCKET_SIZE_DEFAULT)


def get_global_leak_rate():
    return float(os.getenv("GLOBAL_LEAK_RATE") or GLOBAL_LEAK_RATE_DEFAULT)


def create_rabbitmq_connection():
    host = os.environ.get("RABBITMQ_HOST", "localhost")
    user = os.environ.get("RABBITMQ_USER", "user")
    password = os.environ.get("RABBITMQ_PASS", "password")
    credentials = pika.PlainCredentials(user, password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, port=5672, virtual_host='/', credentials=credentials)
    )
    channel = connection.channel()
    return connection, channel

def get_general_queue_name(queue_type, token):

    return f"Queue Service:{queue_type} --- User: {token}"

def get_leakybucket_queue_name():
    """Retorna um nome de fila padrão para o rate limit global."""
    # Esta função agora retorna um nome de fila fixo.
    # A lógica de IP foi removida para focar em um limite global.
    return get_general_queue_name("leaky_bucket", "global")
