import os
import time
import traceback
from functools import wraps
from flask import request, jsonify
from datetime import datetime

import time
from functools import wraps
from flask import request, jsonify
from backpressure import rabbitmq_utils

class LeakyBucketRabbitMQ:
    # Variáveis estáticas para conexão e canal persistentes
    _connection = None
    _channel = None

    @staticmethod
    def _get_persistent_connection():
        # Cria ou retorna conexão/canal persistente
        if LeakyBucketRabbitMQ._connection is None or LeakyBucketRabbitMQ._channel is None or LeakyBucketRabbitMQ._connection.is_closed or LeakyBucketRabbitMQ._channel.is_closed:
            LeakyBucketRabbitMQ._connection, LeakyBucketRabbitMQ._channel = rabbitmq_utils.create_rabbitmq_connection()
        return LeakyBucketRabbitMQ._connection, LeakyBucketRabbitMQ._channel

    @staticmethod
    def _declare_queue_safe(channel, queue_name, bucketcapacity):
        try:
            queue = channel.queue_declare(queue=queue_name, durable=True, arguments={'x-max-length': bucketcapacity})
            return queue
        except Exception as e:
            # Trata erro de precondição (fila já existe com argumentos diferentes)
            if 'PRECONDITION_FAILED' in str(e):
                # Fecha canal/conexão e reabre para garantir canal válido
                try:
                    if hasattr(channel, 'connection') and channel.connection and not channel.connection.is_closed:
                        channel.close()
                        channel.connection.close()
                except Exception:
                    pass
                # Reabre conexão/canal
                from backpressure import rabbitmq_utils
                connection, channel = rabbitmq_utils.create_rabbitmq_connection()
                queue = channel.queue_declare(queue=queue_name, durable=True, passive=True)
                # Atualiza canal persistente
                LeakyBucketRabbitMQ._connection = connection
                LeakyBucketRabbitMQ._channel = channel
                return queue
            else:
                raise

    @staticmethod
    def add_to_global_leaky_bucket(bucketcapacity=int(os.getenv('GLOBAL_BUCKET_SIZE')), queue_name=os.getenv('GLOBAL_QUEUE_NAME')):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):

                try:
                    current_queue = queue_name or rabbitmq_utils.get_leakybucket_queue_name()
                    connection, channel = LeakyBucketRabbitMQ._get_persistent_connection()
                    queue = LeakyBucketRabbitMQ._declare_queue_safe(channel, current_queue, bucketcapacity)
                    current_tokens = queue.method.message_count

                    if current_tokens < bucketcapacity:
                        req_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        message = f'{current_queue}: {req_id}'
                        channel.basic_publish(exchange='', routing_key=current_queue, body=message.encode())
                        return f(*args, **kwargs)
                    else:
                        return jsonify({"status": "error", "message": "Request limit exceeded!"}), 429
                except Exception as e:
                    LeakyBucketRabbitMQ._connection = None
                    LeakyBucketRabbitMQ._channel = None
                    return jsonify({
                        "status": "error",
                        "message": f"Erro interno: {str(e)}",
                        "trace": traceback.format_exc()
                    }), 500

            return wrapped
        return decorator

