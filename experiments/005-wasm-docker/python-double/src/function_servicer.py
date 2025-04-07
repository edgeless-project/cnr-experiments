# SPDX-FileCopyrightText: © 2024 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
# SPDX-License-Identifier: MIT

from enum import Enum
import logging
from urllib.parse import urlparse
from time import sleep

from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2

import services_pb2_grpc
import messages_pb2

logger = logging.getLogger(__name__)


class State(Enum):
    PRE_BOOTED = 1
    BOOTED = 2
    INITIALIZED = 3
    STOPPED = 4
    ERROR = 5


class FunctionServicer(services_pb2_grpc.GuestAPIFunction):
    def __init__(self, function_api):
        self.function_api = function_api
        self.instance_id = None
        self.state = State.PRE_BOOTED

    def Boot(self, request, context):
        logger.info(
            "boot() host_endpoint {} node_id {} function_id {}".format(
                request.guest_api_host_endpoint,
                request.instance_id.node_id,
                request.instance_id.function_id,
            )
        )
        parsed = urlparse(request.guest_api_host_endpoint)
        self.function_api.connect_to_server(
            "{}:{}".format(parsed.hostname, parsed.port), request.instance_id
        )
        self.state = State.BOOTED
        return google_dot_protobuf_dot_empty__pb2.Empty()

    def Init(self, request, context):
        self.check_state(State.BOOTED)
        self.state = State.INITIALIZED
        return google_dot_protobuf_dot_empty__pb2.Empty()

    def Cast(self, request, context):
        self.check_state(State.INITIALIZED)

        tokens = str(request.msg, encoding="utf8").strip().split(" ")
        if len(tokens) >= 1:
            number = float(tokens[0])
            self.function_api.cast(
                alias="output", msg=bytes(str(number * 2.0), encoding="utf8")
            )

        return google_dot_protobuf_dot_empty__pb2.Empty()

    def Call(self, request, context):
        self.check_state(State.INITIALIZED)
        return messages_pb2.CallReturn(type=messages_pb2.CALL_NO_RET)

    def Stop(self, request, context):
        self.check_state(State.INITIALIZED)
        self.state = State.STOPPED
        return google_dot_protobuf_dot_empty__pb2.Empty()

    def check_state(self, state: State):
        """Raise exception if the state is not that specified"""

        if self.state != state:
            self.state = State.ERROR
            raise RuntimeError(
                "expected to be in state {}, actual state {}".format(state, self.state)
            )
