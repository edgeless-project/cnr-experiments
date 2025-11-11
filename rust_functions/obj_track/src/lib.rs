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

type Objects = std::collections::VecDeque<std::collections::HashMap<String, (u32, u32)>>;

#[derive(Default)]
struct State {
    objects: Objects,
}

fn draw_bbox(
    img: &mut image::DynamicImage,
    bbox: [f32; 4],
    pixel: image::Rgba<u8>,
    line_width: u32,
) {
    let img_width = img.width();
    let img_height = img.height();
    let mut pp = |x, y, p| {
        if x < img_width && y < img_height {
            img.put_pixel(x, y, p)
        }
    };

    let left_x = bbox[0].round() as u32;
    let right_x = bbox[2].round() as u32;
    let top_y = bbox[1].round() as u32;
    let bottom_y = bbox[3].round() as u32;
    for x in left_x..=right_x {
        for offset in 0..line_width {
            pp(x, top_y + offset, pixel);
            pp(x, bottom_y - offset, pixel);
        }
    }
    for y in top_y..bottom_y {
        for offset in 0..line_width {
            pp(left_x + offset, y, pixel);
            pp(right_x - offset, y, pixel);
        }
    }
}

fn draw_paths(img: &mut image::DynamicImage, objects: &Objects, line_width: u32) {
    let mut img = img;

    if objects.is_empty() {
        return;
    }

    for label in objects.back().unwrap().keys() {
        let mut last_midpoint: Option<(u32, u32)> = None;
        let color = label_to_color(&label);
        for object in objects {
            if let Some(midpoint) = object.get(label) {
                if let Some(last_midpoint) = last_midpoint {
                    for offset in 0..line_width as i32 {
                        let real_offset = line_width as i32 / 2 - offset;
                        draw_line(
                            &mut img,
                            midpoint.0 as i32,
                            midpoint.1 as i32 + real_offset,
                            last_midpoint.0 as i32,
                            last_midpoint.1 as i32 + real_offset,
                            color,
                        );
                    }
                }

                last_midpoint = Some(midpoint.clone());
            }
        }
    }
}

// Bresenham’s Line Algorithm
fn draw_line(
    img: &mut image::DynamicImage,
    mut x0: i32,
    mut y0: i32,
    x1: i32,
    y1: i32,
    color: image::Rgba<u8>,
) {
    let img_width = img.width() as i32;
    let img_height = img.height() as i32;
    let dx = (x1 - x0).abs();
    let sx = if x0 < x1 { 1 } else { -1 };
    let dy = -(y1 - y0).abs();
    let sy = if y0 < y1 { 1 } else { -1 };
    let mut err = dx + dy;

    loop {
        if x0 >= 0 && x0 < img_width && y0 >= 0 && y0 < img_height {
            img.put_pixel(x0 as u32, y0 as u32, color);
        }
        if x0 == x1 && y0 == y1 {
            break;
        }
        let e2 = 2 * err;
        if e2 >= dy {
            err += dy;
            x0 += sx;
        }
        if e2 <= dx {
            err += dx;
            y0 += sy;
        }
    }
}

fn label_to_color(label: &str) -> image::Rgba<u8> {
    let mut state = std::hash::DefaultHasher::new();
    label.hash(&mut state);
    let hash = state.finish();
    let hash_bytes = hash.to_be_bytes();
    image::Rgba([hash_bytes[0], hash_bytes[1], hash_bytes[2], 0])
}

fn process(input: &Input, conf: &Conf) -> anyhow::Result<Vec<u8>> {
    let vec: Vec<u8> = base64::engine::general_purpose::STANDARD.decode(&input.image_b64)?;
    let mut img = image::load_from_memory(vec.as_slice())?;

    let mut new_objects = std::collections::HashMap::new();
    let mut duplicates = std::collections::HashSet::new();
    for i in 0..input.boxes.len() {
        if i < input.labels.len() {
            let bbox = input.boxes[i];
            let label = input.labels[i].clone();
            draw_bbox(&mut img, bbox, label_to_color(&label), conf.width);

            if duplicates.contains(&label) {
                continue;
            }

            let midpoint_x = (bbox[0] + bbox[2]) as u32 / 2;
            let midpoint_y = (bbox[1] + bbox[3]) as u32 / 2;
            if new_objects
                .insert(label.clone(), (midpoint_x, midpoint_y))
                .is_some()
            {
                new_objects.remove(&label);
                duplicates.insert(label);
            }
        }
    }

    let mut state = STATE.get().unwrap().lock().unwrap();

    // Remove all the objects that are not in the last frame.
    for object in &mut state.objects {
        object.retain(|label, _midpoint| new_objects.contains_key(label));
    }

    state.objects.push_back(new_objects);
    if state.objects.len() >= conf.window as usize {
        state.objects.pop_front();
    }

    draw_paths(&mut img, &state.objects, conf.width);

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
// - next: send an empty message when done
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

        cast("next", &[]);
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
        let _ = STATE.set(std::sync::Mutex::new(State::default()));
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
