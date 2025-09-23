// SPDX-FileCopyrightText: © 2025 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use base64::Engine;
use edgeless_function::*;

struct StateSimFunction;

enum Operation {
    Increment,
    Sin,
}

struct Conf {
    /// True: the state is local. False: it is read from "state".
    is_local: bool,
    /// Vector size, in f32.
    vec_size: usize,
    /// Operation type.
    operation: Operation,
}

struct State {
    /// Pseudo-random number generator.
    lcg: edgeless_function::lcg::Lcg,
    /// State (a vector of floats).
    vector: Vec<f32>,
}

static CONF: std::sync::OnceLock<Conf> = std::sync::OnceLock::new();
static STATE: std::sync::OnceLock<std::sync::Mutex<State>> = std::sync::OnceLock::new();

impl EdgeFunction for StateSimFunction {
    fn handle_cast(_src: InstanceId, msg: &[u8]) {
        let conf = CONF.get().unwrap();
        let mut state = STATE.get().unwrap().lock().unwrap();

        if conf.is_local {
            if state.vector.is_empty() {
                // First time: create a new vector.
                let mut new_vector =
                    edgeless_function::lcg::random_vector(&mut state.lcg, conf.vec_size);
                std::mem::swap(&mut state.vector, &mut new_vector);
            } else {
                // Non-first-time: perform operation.
                match &conf.operation {
                    Operation::Increment => {
                        for elem in &mut state.vector {
                            *elem += 1.0_f32;
                        }
                    }
                    Operation::Sin => {
                        for elem in &mut state.vector {
                            *elem = elem.sin();
                        }
                    }
                };
            }
        } else {
            // Retrieve the state.
            assert!(state.vector.is_empty());

            let res = call("state", b"state");
            let vector = if let CallRet::Reply(msg) = res {
                if let Ok(vec_bytes) =
                    base64::engine::general_purpose::STANDARD.decode(msg.as_ref())
                {
                    vec_bytes
                        .chunks_exact(4)
                        .map(TryInto::try_into)
                        .map(Result::unwrap)
                        .map(f32::from_be_bytes)
                        .collect()
                } else {
                    edgeless_function::lcg::random_vector(&mut state.lcg, conf.vec_size)
                }
            } else {
                edgeless_function::lcg::random_vector(&mut state.lcg, conf.vec_size)
            };

            // Increment by one each element.
            for elem in &mut state.vector {
                *elem += 1.0_f32;
            }

            // Convert the vector using Base64 and save it back.
            let vec_bytes = vector
                .iter()
                .map(|x| x.to_be_bytes())
                .flatten()
                .collect::<Vec<u8>>();

            cast(
                "state",
                base64::engine::general_purpose::STANDARD
                    .encode(vec_bytes)
                    .as_bytes(),
            );
        }

        // Send the message received when one.
        cast("out", msg);
    }

    fn handle_call(_src: InstanceId, _encoded_message: &[u8]) -> CallRet {
        CallRet::NoReply
    }

    // example of payload:
    // local=true,vec_size=1000,operation=sin
    fn handle_init(payload: Option<&[u8]>, _serialized_state: Option<&[u8]>) {
        // edgeless_function::init_logger();

        let arguments = edgeless_function::init_payload_to_args(payload);

        let local = edgeless_function::arg_to_bool("local", &arguments);

        let vec_size = arguments
            .get("vec_size")
            .unwrap_or(&"100")
            .parse::<usize>()
            .unwrap_or(100);

        let operation = match arguments.get("operation").unwrap_or(&"") {
            &"sin" => Operation::Sin,
            &"incr" => Operation::Increment,
            _ => Operation::Increment,
        };

        let _ = CONF.set(Conf {
            is_local: local,
            vec_size,
            operation,
        });

        let lcg = edgeless_function::lcg::Lcg::new(42);

        let _ = STATE.set(std::sync::Mutex::new(State {
            lcg,
            vector: vec![],
        }));
    }

    fn handle_stop() {
        // Noop
    }
}

edgeless_function::export!(StateSimFunction);
