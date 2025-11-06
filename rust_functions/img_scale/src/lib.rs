// SPDX-FileCopyrightText: © 2025 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use base64::Engine;
use edgeless_function::*;

struct ImgScale;

enum ResizeType {
    Preserve,
    Exact,
    Fill,
}

struct Conf {
    /// True: call log directive at every new image received.
    is_log_enabled: bool,

    resize_type: ResizeType,
    width: u32,
    height: u32,
}

fn process(msg: &[u8], conf: &Conf) -> anyhow::Result<Vec<u8>> {
    let vec: Vec<u8> = base64::engine::general_purpose::STANDARD.decode(msg)?;
    let img = image::load_from_memory(vec.as_slice())?;

    let filter = image::imageops::FilterType::Triangle;
    let img_resized = match conf.resize_type {
        ResizeType::Preserve => img.resize(conf.width, conf.height, filter),
        ResizeType::Exact => img.resize_exact(conf.width, conf.height, filter),
        ResizeType::Fill => img.resize_to_fill(conf.width, conf.height, filter),
    };

    let mut bytes: Vec<u8> = Vec::new();
    img_resized.write_to(
        &mut std::io::Cursor::new(&mut bytes),
        image::ImageFormat::Jpeg,
    )?;

    if conf.is_log_enabled {
        log::info!(
            "image resized from {}x{} to {}x{} ({} bytes)",
            img.width(),
            img.height(),
            img_resized.width(),
            img_resized.height(),
            bytes.len()
        );
    }

    Ok(base64::engine::general_purpose::STANDARD
        .encode(bytes)
        .as_bytes()
        .to_vec())
}

static CONF: std::sync::OnceLock<Conf> = std::sync::OnceLock::new();

// Expected to receive base64-encoded images via cast().
//
// Outputs:
// - out: base64-encoded resized image, in JPEG
// - err: human-readable error if the input is not valid
impl EdgeFunction for ImgScale {
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
    // log=false,resize_type=preserve,width=100,height=100
    fn handle_init(payload: Option<&[u8]>, _serialized_state: Option<&[u8]>) {
        let args = edgeless_function::init_payload_to_args(payload);

        let is_log_enabled = edgeless_function::arg_to_bool("log", &args);

        if is_log_enabled {
            edgeless_function::init_logger();
        }

        let resize_type = match args.get("resize_type").unwrap_or(&"preserve") {
            &"preserve" => ResizeType::Preserve,
            &"exact" => ResizeType::Exact,
            &"fill" => ResizeType::Fill,
            _ => ResizeType::Preserve,
        };

        let width = args
            .get("width")
            .unwrap_or(&"100")
            .parse::<u32>()
            .unwrap_or(100);
        let height = args
            .get("height")
            .unwrap_or(&"100")
            .parse::<u32>()
            .unwrap_or(100);

        let _ = CONF.set(Conf {
            is_log_enabled,
            resize_type,
            width,
            height,
        });
    }

    fn handle_stop() {
        // Noop
    }
}

edgeless_function::export!(ImgScale);

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
