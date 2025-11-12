// SPDX-FileCopyrightText: © 2025 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use edgeless_function::*;

struct FlowControl;

struct Conf {
    /// Number of pending messages that are ideally allowed to be in flight.
    window: usize,
    /// Number of incoming messages after which the flow control window resets.
    timeout: usize,
    /// If true then forward the dropped message to the "drop" output channel.
    drop: bool,
}

#[derive(Default)]
struct State {
    in_flight: usize,
    zero_reached: bool,
    rcv_since_zero_reached: usize,
}

static CONF: std::sync::OnceLock<Conf> = std::sync::OnceLock::new();
static STATE: std::sync::OnceLock<std::sync::Mutex<State>> = std::sync::OnceLock::new();

// Drop incoming messages if there are too many in flight already.
//
// Reset the flow control window after a timeout, expresse in terms of
// incoming messages during which the number of in-flight messages never
// reached zero.
//
// A message is considered not in flight anymore when an empty message is
// received.
//
// Outputs:
// - out: forwarded message
// - err: human-readable message when an incoming message is dropped
// - drop: dropped message
impl EdgeFunction for FlowControl {
    fn handle_cast(_src: InstanceId, msg: &[u8]) {
        let conf = CONF.get().unwrap();
        let mut state = STATE.get().unwrap().lock().unwrap();

        if msg.is_empty() {
            if state.in_flight > 0 {
                state.in_flight -= 1;
            }
            if state.in_flight == 0 {
                state.zero_reached = true;
            }
        } else {
            if state.zero_reached {
                state.zero_reached = false;
                state.rcv_since_zero_reached = 0;
            }
            state.rcv_since_zero_reached += 1;

            if state.rcv_since_zero_reached >= conf.timeout {
                state.in_flight = 0;
                state.rcv_since_zero_reached = 0;
            }

            if state.in_flight >= conf.window {
                if conf.drop {
                    cast("drop", msg);
                }
                cast(
                    "err",
                    format!("dropped message of size {} bytes", msg.len())
                        .as_str()
                        .as_bytes(),
                );
            } else {
                state.in_flight += 1;
                cast("out", msg);
            }
        }
    }

    fn handle_call(_src: InstanceId, _encoded_message: &[u8]) -> CallRet {
        CallRet::NoReply
    }

    // example of payload, with default values:
    // window=5,timeout=50,drop=false
    fn handle_init(payload: Option<&[u8]>, _serialized_state: Option<&[u8]>) {
        let args = edgeless_function::init_payload_to_args(payload);

        let is_log_enabled = edgeless_function::arg_to_bool("log", &args);

        if is_log_enabled {
            edgeless_function::init_logger();
        }

        let window = args
            .get("window")
            .unwrap_or(&"5")
            .parse::<usize>()
            .unwrap_or(5);
        let timeout = args
            .get("timeout")
            .unwrap_or(&"50")
            .parse::<usize>()
            .unwrap_or(50);
        let drop = edgeless_function::arg_to_bool("drop", &args);

        let _ = CONF.set(Conf {
            window,
            timeout,
            drop,
        });
        let _ = STATE.set(std::sync::Mutex::new(State::default()));
    }

    fn handle_stop() {
        // Noop
    }
}

edgeless_function::export!(FlowControl);
