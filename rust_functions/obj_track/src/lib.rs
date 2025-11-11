// SPDX-FileCopyrightText: © 2025 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use std::hash::Hash;
use std::hash::Hasher;

use base64::Engine;
use edgeless_function::*;
use image::GenericImage;

struct ObjTrack;

struct Conf {
    /// True: call log directive at every new image received.
    is_log_enabled: bool,
    /// Number of images to keep in.
    window: u32,
    /// Width of the bounding box.
    width: u32,
}

#[derive(serde::Deserialize, serde::Serialize)]
struct Input {
    boxes: Vec<[f32; 4]>,
    labels: Vec<String>,
    scores: Vec<f32>,
    image_b64: String,
}

struct State {}

fn draw_bbox(img: &mut image::DynamicImage, bbox: [f32; 4], pixel: image::Rgba<u8>, width: u32) {
    let left_x = bbox[0].round() as u32;
    let right_x = bbox[2].round() as u32;
    let top_y = bbox[1].round() as u32;
    let bottom_y = bbox[3].round() as u32;
    for x in left_x..=right_x {
        for offset in 0..width {
            img.put_pixel(x, top_y + offset, pixel);
            img.put_pixel(x, bottom_y - offset, pixel);
        }
    }
    for y in top_y..bottom_y {
        for offset in 0..width {
            img.put_pixel(left_x + offset, y, pixel);
            img.put_pixel(right_x - offset, y, pixel);
        }
    }
}

fn process(input: &Input, conf: &Conf) -> anyhow::Result<Vec<u8>> {
    let vec: Vec<u8> = base64::engine::general_purpose::STANDARD.decode(&input.image_b64)?;
    let mut img = image::load_from_memory(vec.as_slice())?;

    for i in 0..input.boxes.len() {
        if i < input.labels.len() {
            let bbox = input.boxes[i];
            let mut state = std::hash::DefaultHasher::new();
            input.labels[i].hash(&mut state);
            let hash = state.finish();
            let hash_bytes = hash.to_be_bytes();
            draw_bbox(
                &mut img,
                bbox,
                image::Rgba([hash_bytes[0], hash_bytes[1], hash_bytes[2], 0]),
                conf.width,
            );
        }
    }

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

// Track objects in a sequence of frames by drawing a bounding box and the
// path. Works for objects of different labels, but ignores multiple instances
// of the same object.
//
// Expects to receive an `Input` JSON structure via cast().
//
// Outputs:
// - out: base64-encoded resized image, in JPEG
// - err: human-readable error if the input is not valid
impl EdgeFunction for ObjTrack {
    fn handle_cast(_src: InstanceId, msg: &[u8]) {
        let conf = CONF.get().unwrap();

        match core::str::from_utf8(msg) {
            Ok(msg) => match serde_json::from_str::<Input>(msg) {
                Ok(input) => match process(&input, &conf) {
                    Ok(output) => {
                        cast("out", &output);
                    }
                    Err(err) => cast("err", err.to_string().as_bytes()),
                },
                Err(err) => cast(
                    "err",
                    format!("invalid JSON input received at obj_track: {}", err)
                        .as_str()
                        .as_bytes(),
                ),
            },
            Err(err) => cast(
                "err",
                format!("non-string received as input to obj_track: {}", err)
                    .as_str()
                    .as_bytes(),
            ),
        }
    }

    fn handle_call(_src: InstanceId, _encoded_message: &[u8]) -> CallRet {
        CallRet::NoReply
    }

    // example of payload, with default values:
    // log=false,window=5,width=3
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
        let width = args
            .get("width")
            .unwrap_or(&"3")
            .parse::<u32>()
            .unwrap_or(3);

        let _ = CONF.set(Conf {
            is_log_enabled,
            window,
            width,
        });
    }

    fn handle_stop() {
        // Noop
    }
}

edgeless_function::export!(ObjTrack);

#[cfg(test)]
mod tests {
    #[test]
    fn test_obj_track() -> anyhow::Result<()> {
        Ok(())
    }
}
