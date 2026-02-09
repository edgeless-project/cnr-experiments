// SPDX-FileCopyrightText: © 2025 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use actix_multipart::Multipart;
use actix_web::http::Uri;
use actix_web::mime;
use actix_web::{
    App, HttpRequest, HttpResponse, HttpServer, Responder,
    http::header::{self, ContentType},
    web,
};
use bytes::Bytes;
use clap::Parser;
use futures_util::StreamExt;
use image::ImageFormat;
use image::codecs::jpeg::JpegEncoder;
use once_cell::sync::Lazy;
use std::io::Write;
use std::str::FromStr;
use std::{
    sync::{Arc, Mutex},
    time::Duration,
};
use tokio::time::sleep;

#[derive(Debug, clap::Parser)]
#[command(long_about = "Simple image viewer from HTTP POST commands")]
struct Args {
    /// Web server URL.
    #[arg(short, long, default_value_t = String::from("http://localhost:3000"))]
    url: String,
    /// Save timestamps to this file.
    #[arg(short, long, default_value_t = String::default())]
    output: String,
    /// Number of workers.
    #[arg(short, long, default_value_t = std::thread::available_parallelism().unwrap().into())]
    workers: usize,
    /// Do not publish incoming images.
    #[arg(long, default_value_t = false)]
    dry: bool,
}

fn print_timestamp(output: Option<&mut std::fs::File>) {
    if let Some(mut output) = output {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default();
        let _ = writeln!(&mut output, "{}", now.as_secs_f64());
    }
}

#[derive(Default)]
struct State {
    last_frame: Option<Bytes>,
    output: Option<std::fs::File>,
    dry: bool,
}

static STATE: Lazy<Arc<Mutex<State>>> = Lazy::new(|| Arc::new(Mutex::new(State::default())));

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let args = Args::parse();

    {
        let mut state = STATE.lock().unwrap();

        if !args.output.is_empty() {
            println!("Saving timestamps to '{}'", args.output);
            state.output = Some(std::fs::File::create(&args.output)?);
        }
        state.dry = args.dry;
    }

    println!("Server running at {}", args.url);

    match Uri::from_str(&args.url) {
        Ok(uri) => {
            HttpServer::new(|| {
                App::new()
                    .route("/", web::get().to(index))
                    .route("/post", web::post().to(post))
                    .route("/upload", web::post().to(upload))
                    .route("/stream", web::get().to(stream))
            })
            .workers(args.workers)
            .bind((
                uri.host().unwrap_or(&"0.0.0.0"),
                uri.port_u16().unwrap_or(3000),
            ))?
            .run()
            .await
        }
        Err(_) => Err(std::io::Error::other("invalid URL specified")),
    }
}

async fn index() -> impl Responder {
    HttpResponse::Ok().content_type(ContentType::html()).body(
        r#"
            <!DOCTYPE html>
            <html>
            <body>
                <h1>Live Stream</h1>
                <img src="/stream" />
            </body>
            </html>
        "#,
    )
}

async fn post(mut payload: web::Payload) -> impl Responder {
    let dry;
    {
        let mut state = STATE.lock().unwrap();
        print_timestamp(state.output.as_mut());
        dry = state.dry;
    }
    if dry {
        payload.count().await;
        return HttpResponse::Ok().body("OK");
    }
    let mut data = web::BytesMut::new();
    while let Some(Ok(chunk)) = payload.next().await {
        data.extend_from_slice(&chunk);
    }

    let image_data = data.freeze();

    STATE.lock().unwrap().last_frame = Some(image_data);

    return HttpResponse::Ok().body("Image posted");
}

async fn upload(mut payload: Multipart) -> impl Responder {
    while let Some(Ok(mut field)) = payload.next().await {
        if let Some(mime) = field.content_type().cloned() {
            if mime.type_() == mime::IMAGE {
                let mut data = web::BytesMut::new();
                while let Some(Ok(chunk)) = field.next().await {
                    data.extend_from_slice(&chunk);
                }

                let image_data = data.freeze();

                // Convert to JPEG if not already JPEG
                let final_data = match mime.subtype().as_str() {
                    "jpeg" | "jpg" => image_data,
                    "png" => {
                        match image::load_from_memory_with_format(&image_data, ImageFormat::Png) {
                            Ok(img) => {
                                let mut buf = Vec::new();
                                let mut encoder = JpegEncoder::new(&mut buf);
                                if encoder.encode_image(&img).is_ok() {
                                    Bytes::from(buf)
                                } else {
                                    return HttpResponse::InternalServerError()
                                        .body("Failed to encode JPEG");
                                }
                            }
                            Err(_) => return HttpResponse::BadRequest().body("Invalid PNG image"),
                        }
                    }
                    _ => return HttpResponse::BadRequest().body("Unsupported image type"),
                };

                STATE.lock().unwrap().last_frame = Some(final_data);

                return HttpResponse::Ok().body("Image uploaded");
            }
        }
    }

    HttpResponse::BadRequest().body("Expected image field")
}

async fn stream(_req: HttpRequest) -> impl Responder {
    let stream = async_stream::stream! {
        loop {
            sleep(Duration::from_millis(100)).await;

            let maybe_img = {
                let state = STATE.lock().unwrap();
                state.last_frame.clone()
            };

            if let Some(img) = maybe_img {
                let header = format!(
                    "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: {}\r\n\r\n",
                    img.len()
                );
                yield Ok::<_, actix_web::Error>(Bytes::from(header));
                yield Ok(Bytes::from(img));
                yield Ok(Bytes::from("\r\n"));
            }
        }
    };

    HttpResponse::Ok()
        .insert_header((
            header::CONTENT_TYPE,
            "multipart/x-mixed-replace; boundary=frame",
        ))
        .streaming(stream)
}
