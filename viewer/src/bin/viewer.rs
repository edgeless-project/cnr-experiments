use actix_multipart::Multipart;
use actix_web::mime;
use actix_web::{
    http::header::{self, ContentType},
    web, App, HttpRequest, HttpResponse, HttpServer, Responder,
};
use bytes::Bytes;
use futures_util::StreamExt;
use image::codecs::jpeg::JpegEncoder;
use image::ImageFormat;
use once_cell::sync::Lazy;
use std::{
    sync::{Arc, Mutex},
    time::Duration,
};
use tokio::time::sleep;

static LAST_FRAME: Lazy<Arc<Mutex<Option<Bytes>>>> = Lazy::new(|| Arc::new(Mutex::new(None)));

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("Server running at http://localhost:3000");

    HttpServer::new(|| {
        App::new()
            .route("/", web::get().to(index))
            .route("/upload", web::post().to(upload))
            .route("/stream", web::get().to(stream))
    })
    .bind(("0.0.0.0", 3000))?
    .run()
    .await
}

async fn index() -> impl Responder {
    HttpResponse::Ok().content_type(ContentType::html()).body(
        r#"
            <!DOCTYPE html>
            <html>
            <body>
                <h1>Live Stream</h1>
                <img src="/stream" />
                <img src="/stream" />
            </body>
            </html>
        "#,
    )
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

                let mut frame = LAST_FRAME.lock().unwrap();
                *frame = Some(final_data);

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
                let lock = LAST_FRAME.lock().unwrap();
                lock.clone()
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
