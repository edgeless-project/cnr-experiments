# SPDX-FileCopyrightText: © 2024 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
# SPDX-License-Identifier: MIT

import logging
from concurrent import futures
import sys
import argparse

import grpc

import services_pb2_grpc
import messages_pb2
import function_servicer

from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2

logger = logging.getLogger(__name__)


class Function:
    def __init__(self, port: int, max_workers: int) -> None:
        """Create a function instance exposing a GuestAPIFunction server and using a GuestAPIHost client"""

        # The client and instance ID will be initialized in connect_to_server()
        self.client = None
        self.instance_id = None

        # Create the server
        logger.info(
            "starting server at [::]:{} with max {} workers".format(port, max_workers)
        )
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
        services_pb2_grpc.add_GuestAPIFunctionServicer_to_server(
            function_servicer.FunctionServicer(self), self.server
        )
        self.server.add_insecure_port("[::]:{}".format(port))
        self.server.start()

    def connect_to_server(
        self, host_endpoint: str, instance_id: messages_pb2.InstanceId
    ) -> None:
        # Create the client
        logger.info("starting a client towards remote host at {}".format(host_endpoint))
        channel = grpc.insecure_channel(host_endpoint)
        self.client = services_pb2_grpc.GuestAPIHostStub(channel)

        # Save the instance ID
        self.instance_id = instance_id

    def cast(self, alias: str, msg: bytes) -> None:
        assert self.client is not None
        self.client.Cast(
            messages_pb2.OutputEventData(
                originator=self.instance_id, alias=alias, msg=msg
            )
        )

    def cast_raw(self, node_id: str, function_id: str, msg: bytes) -> None:
        assert self.client is not None
        self.client.CastRaw(
            messages_pb2.OutputEventDataRaw(
                originator=self.instance_id,
                dst=messages_pb2.InstanceId(node_id=node_id, function_id=function_id),
                msg=msg,
            )
        )

    def call(self, alias: str, msg: bytes) -> messages_pb2.CallReturn:
        assert self.client is not None
        return self.client.Call(
            messages_pb2.OutputEventData(
                originator=self.instance_id, alias=alias, msg=msg
            )
        )

    def call_raw(
        self, node_id: str, function_id: str, msg: bytes
    ) -> messages_pb2.CallReturn:
        assert self.client is not None
        return self.client.CallRaw(
            messages_pb2.OutputEventDataRaw(
                originator=self.instance_id,
                instance_id=messages_pb2.InstanceId(
                    node_id=node_id, function_id=function_id
                ),
                msg=msg,
            )
        )

    def telemetry_log(self, log_level: int, target: str, msg: str) -> None:
        assert self.client is not None
        self.client.TelemetryLog(
            messages_pb2.TelemetryLogEvent(
                originator=self.instance_id, log_level=log_level, target=target, msg=msg
            )
        )

    def slf(self) -> messages_pb2.InstanceId:
        return self.instance_id

    def delayed_cast(self, delay: int, alias: str, msg: bytes) -> None:
        assert self.client is not None
        self.client.DelayedCast(
            messages_pb2.DelayedEventData(
                originator=self.instance_id, alias=alias, msg=msg, delay=delay
            )
        )

    def sync(self, serialized_state: bytes) -> None:
        assert self.client is not None
        self.client.Sync(
            messages_pb2.SyncData(
                originator=self.instance_id, serialized_state=serialized_state
            )
        )

    def wait(self) -> None:
        self.server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    logging.getLogger("function_servicer").setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(
        "Run an EDGELESS function instance",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--log-level", type=str, default="WARNING", help="Set the log level"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7101,
        help="Listening port",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Maximum number of workers",
    )
    args = parser.parse_args()

    function = Function(port=args.port, max_workers=args.max_workers)
    function.wait()
