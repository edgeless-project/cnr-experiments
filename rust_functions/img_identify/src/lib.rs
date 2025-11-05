// SPDX-FileCopyrightText: © 2025 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use base64::Engine;
use edgeless_function::*;

struct ImgIdentify;

struct Conf {
    /// True: call log directive at every new image received.
    is_log_enabled: bool,
}

#[derive(Debug, serde::Serialize)]
struct ImgInfo {
    width: u32,
    height: u32,
}

fn process(msg: &[u8]) -> anyhow::Result<ImgInfo> {
    let vec: Vec<u8> = base64::engine::general_purpose::STANDARD.decode(msg)?;
    let img = image::load_from_memory(vec.as_slice())?;
    Ok(ImgInfo {
        width: img.width(),
        height: img.height(),
    })
}

static CONF: std::sync::OnceLock<Conf> = std::sync::OnceLock::new();

// Expected to receive base64-encoded images via cast().
//
// Outputs:
// - info: JSON-encoded image characteristics
// - forward: input received
// - err: human-readable error if the input is not valid
impl EdgeFunction for ImgIdentify {
    fn handle_cast(_src: InstanceId, msg: &[u8]) {
        let conf = CONF.get().unwrap();

        match process(msg) {
            Ok(img_info) => {
                if let Ok(json_info) = serde_json::to_string(&img_info) {
                    if conf.is_log_enabled {
                        log::info!("image received: {:?}", json_info);
                    }
                    cast("info", json_info.as_bytes());
                }
                cast("forward", msg);
            }
            Err(err) => cast("err", err.to_string().as_bytes()),
        }
    }

    fn handle_call(_src: InstanceId, _encoded_message: &[u8]) -> CallRet {
        CallRet::NoReply
    }

    // example of payload:
    // log=true
    fn handle_init(payload: Option<&[u8]>, _serialized_state: Option<&[u8]>) {
        let args = edgeless_function::init_payload_to_args(payload);
        let is_log_enabled = edgeless_function::arg_to_bool("log", &args);

        if is_log_enabled {
            edgeless_function::init_logger();
        }

        let _ = CONF.set(Conf { is_log_enabled });
    }

    fn handle_stop() {
        // Noop
    }
}

edgeless_function::export!(ImgIdentify);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_img_identify() -> anyhow::Result<()> {
        let data = std::fs::read("image.png")?;

        let res = process(
            base64::engine::general_purpose::STANDARD
                .encode(data)
                .as_bytes(),
        );
        println!("{:?}", res);

        assert!(process(&vec![]).is_err());

        Ok(())
    }
}
