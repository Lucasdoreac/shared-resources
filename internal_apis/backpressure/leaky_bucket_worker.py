# internal_apis/backpressure/leaky_bucket_worker.py
import logging
import os
import signal
from threading import Event
from backpressure.rabbitmq_utils import create_rabbitmq_connection
from backpressure.rabbitmq_utils import get_leakybucket_queue_name

def start_leaky_bucket_worker(leakrate, bucketcapacity, queue_name=None, stop_event=None):
    if leakrate <= 0 or bucketcapacity <= 0:
        raise ValueError("Intervalo e capacidade do bucket devem ser positivos")
    stop_event = stop_event if stop_event is not None else Event()
    if queue_name is None:
        queue_name = get_leakybucket_queue_name()

    connection, channel = create_rabbitmq_connection()
    try:
        channel.queue_declare(queue=queue_name, durable=True, arguments={'x-max-length': bucketcapacity})
        while not stop_event.is_set():
            method_frame, _, _ = channel.basic_get(queue=queue_name)
            if method_frame:
                channel.basic_ack(method_frame.delivery_tag)
            # BlockingConnection.sleep mantém heartbeats durante a espera.
            connection.sleep(leakrate)
    finally:
        if connection.is_open:
            connection.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stop = Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    start_leaky_bucket_worker(
        float(os.environ["GLOBAL_LEAK_RATE"]),
        int(os.environ["GLOBAL_BUCKET_SIZE"]),
        os.getenv("GLOBAL_QUEUE_NAME"),
        stop_event=stop,
    )

