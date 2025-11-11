// SPDX-FileCopyrightText: © 2025 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use base64::Engine;
use edgeless_function::*;

struct ObjTrack;

enum ResizeType {
    Preserve,
    Exact,
    Fill,
}

struct Conf {
    /// True: call log directive at every new image received.
    is_log_enabled: bool,
    /// Number of images to keep in
    window: u32,
}

struct State {}

fn process(msg: &[u8], conf: &Conf) -> anyhow::Result<Vec<u8>> {
    let vec: Vec<u8> = base64::engine::general_purpose::STANDARD.decode(msg)?;
    let img = image::load_from_memory(vec.as_slice())?;

    let mut bytes: Vec<u8> = Vec::new();
    img.write_to(
        &mut std::io::Cursor::new(&mut bytes),
        image::ImageFormat::Jpeg,
    )?;

    if conf.is_log_enabled {
        log::info!(
            "processed {}x{} image ({} bytes)",
            img.width(),
            img.height(),
            bytes.len()
        );
    }

    Ok(base64::engine::general_purpose::STANDARD
        .encode(bytes)
        .as_bytes()
        .to_vec())
}

static CONF: std::sync::OnceLock<Conf> = std::sync::OnceLock::new();
static STATE: std::sync::OnceLock<std::sync::Mutex<State>> = std::sync::OnceLock::new();

// Expected to receive base64-encoded images via cast().
//
// Outputs:
// - out: base64-encoded resized image, in JPEG
// - err: human-readable error if the input is not valid
impl EdgeFunction for ObjTrack {
    fn handle_cast(_src: InstanceId, msg: &[u8]) {
        let conf = CONF.get().unwrap();

        match process(msg, &conf) {
            Ok(img_resized) => {
                cast("out", &img_resized);
            }
            Err(err) => cast("err", err.to_string().as_bytes()),
        }
    }

    fn handle_call(_src: InstanceId, _encoded_message: &[u8]) -> CallRet {
        CallRet::NoReply
    }

    // example of payload, with default values:
    // log=false,window=5
    fn handle_init(payload: Option<&[u8]>, _serialized_state: Option<&[u8]>) {
        let args = edgeless_function::init_payload_to_args(payload);

        let is_log_enabled = edgeless_function::arg_to_bool("log", &args);

        if is_log_enabled {
            edgeless_function::init_logger();
        }

        let window = args
            .get("window")
            .unwrap_or(&"5")
            .parse::<u32>()
            .unwrap_or(5);

        let _ = CONF.set(Conf {
            is_log_enabled,
            window,
        });
    }

    fn handle_stop() {
        // Noop
    }
}

#[allow(clippy::unsafe_op_in_unsafe_fn)]
edgeless_function::export!(ObjTrack);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_img_identify() -> anyhow::Result<()> {
        let data = std::fs::read("image.png")?;
        let conf = Conf {
            is_log_enabled: false,
            resize_type: ResizeType::Preserve,
            width: 1000,
            height: 1000,
        };

        let res = process(
            base64::engine::general_purpose::STANDARD
                .encode(data)
                .as_bytes(),
            &conf,
        )?;

        let decoded = base64::engine::general_purpose::STANDARD.decode(res)?;

        let img = image::ImageReader::new(std::io::Cursor::new(decoded))
            .with_guessed_format()?
            .decode()?;

        assert_eq!(1000, img.width());
        assert_eq!(625, img.height());

        assert!(process(&vec![], &conf).is_err());

        Ok(())
    }
}
