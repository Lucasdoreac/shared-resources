# internal_apis/backpressure/leaky_bucket_worker.py
import time
from backpressure.rabbitmq_utils import create_rabbitmq_connection
from backpressure.rabbitmq_utils import get_leakybucket_queue_name
from flask import request
import os

def start_leaky_bucket_worker(leakrate, queue_name=None):
    if queue_name is None:
        queue_name = get_leakybucket_queue_name()

    print(f"[*] Worker iniciado. Ouvindo a fila: {queue_name}")

    connection, channel = create_rabbitmq_connection()
    channel.queue_delete(queue=queue_name)
    channel.queue_declare(queue=queue_name, durable=True, arguments={'x-max-length': 5})

    log_file_path = os.path.join(os.path.dirname(__file__), 'test_logs')

    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue_name)
        if method_frame:
            print(f"Mensagem consumida: {body.decode()}")  # Log para depuração
            with open(log_file_path, "a") as f:
                f.write(body.decode() + "\n")
            channel.basic_ack(method_frame.delivery_tag)
        else:
            print("Nenhuma mensagem na fila.")  # Log para depuração
        time.sleep(leakrate)

if __name__ == "__main__":
    start_leaky_bucket_worker(1, queue_name='global')
