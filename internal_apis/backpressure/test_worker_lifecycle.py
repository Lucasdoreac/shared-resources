from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import pytest

from backpressure import leaky_bucket_worker as worker


class StopProbe(Exception):
    pass


def run_probe(messages):
    connection = Mock(is_open=True)
    channel = Mock()
    channel.basic_get.side_effect = [*messages, StopProbe()]
    with patch.object(worker, "create_rabbitmq_connection", return_value=(connection, channel)):
        with pytest.raises(StopProbe):
            worker.start_leaky_bucket_worker(0.3, 5, "isolated-worker-test")
    return connection, channel


def test_start_preserves_existing_queue():
    _, channel = run_probe([])
    channel.queue_delete.assert_not_called()
    channel.queue_declare.assert_called_once_with(
        queue="isolated-worker-test", durable=True, arguments={"x-max-length": 5}
    )


def test_each_consumed_token_waits_for_the_leak_interval():
    messages = [(SimpleNamespace(delivery_tag=i), None, b"token") for i in (1, 2)]
    connection, channel = run_probe(messages)
    assert channel.basic_ack.call_args_list == [call(1), call(2)]
    assert connection.sleep.call_args_list == [call(0.3), call(0.3)]


def test_failure_closes_worker_connection():
    connection, _ = run_probe([])
    connection.close.assert_called_once_with()
