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
    @staticmethod
    def rate_limit_by_leaky_bucket(bucketcapacity, queue_name=None):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                try:

                    current_queue = queue_name
                    if current_queue is None:
                        current_queue = rabbitmq_utils.get_leakybucket_queue_name()

                    connection, channel = rabbitmq_utils.create_rabbitmq_connection()
                    queue = channel.queue_declare(queue=current_queue, durable=True, arguments={'x-max-length': bucketcapacity})
                    current_tokens = queue.method.message_count

                    if current_tokens < bucketcapacity:

                        req_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        message = f'{current_queue}: {req_id}'
                        channel.basic_publish(exchange='', routing_key=current_queue, body=message.encode())
                        connection.close()

                        return f(*args, **kwargs)
                    else:
                        connection.close()
                        return jsonify({"status": "error", "message": "Request limit exceeded!"}), 429
                except Exception as e:
                    return jsonify({
                        "status": "error",
                        "message": f"Erro interno: {str(e)}",
                        "trace": traceback.format_exc()
                    }), 500

            return wrapped
        return decorator

    @staticmethod
    def register_global_leaky_bucket(app, bucketcapacity, queue_name=None):
        """
        Registra o rate limit do leaky bucket globalmente para todos os endpoints do Flask.
        Pode ser chamado no setup do app, sem afetar o uso do decorator em testes.
        """

        @app.before_request
        def global_leaky_bucket():
            decorator = LeakyBucketRabbitMQ.rate_limit_by_leaky_bucket(bucketcapacity, queue_name)

            # Função dummy apenas para aplicar o decorator
            @decorator
            def dummy():
                return None

            resp = dummy()
            if resp is not None:
                return resp
            return None