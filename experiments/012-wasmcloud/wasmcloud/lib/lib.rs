use std::{thread, time};
use wasmcloud_component::http::ErrorCode;
use wasmcloud_component::wasi::keyvalue::*;
use wasmcloud_component::HostRng;
use wasmcloud_component::{http, info};

#[derive(Debug)]
enum Operation {
    Increment,
    Sin,
    None,
    IncMean,
    MinMax,
}

fn parse_query(query: &str) -> std::collections::HashMap<&str, String> {
    let tokens = query.split(',');
    let mut arguments = std::collections::HashMap::new();
    for token in tokens {
        let mut inner_tokens = token.split('=');
        if let Some(key) = inner_tokens.next() {
            if let Some(value) = inner_tokens.next() {
                arguments.insert(key, value.to_string());
            }
        }
    }
    arguments
}

fn rand_vector(size: usize) -> Vec<f32> {
    let mut vector = vec![];
    for _ in 0..size {
        let rnd_val = HostRng::random32() as f32 / u32::MAX as f32;
        vector.push(rnd_val);
    }
    vector
}

struct Component;

http::export!(Component);

// Example:
//
// curl "localhost:8000?name=Alice,size=1000,operation=sin,sleep=1000"
//
impl http::Server for Component {
    fn handle(
        request: http::IncomingRequest,
    ) -> http::Result<http::Response<impl http::OutgoingBody>> {
        // Parse query into function arguments.
        let (parts, _body) = request.into_parts();
        let query = parts
            .uri
            .query()
            .map(ToString::to_string)
            .unwrap_or_default();

        let args = parse_query(&query);
        info!("query received: {args:?}");
        let name = args.get("name").cloned().unwrap_or(String::from("unknown"));
        let size = args
            .get("size")
            .cloned()
            .unwrap_or(String::from("10"))
            .parse::<usize>()
            .unwrap_or(10);
        let operation = match args.get("operation") {
            None => Operation::None,
            Some(val) => match val.as_str() {
                "sin" => Operation::Sin,
                "increment" => Operation::Increment,
                "inc-mean" => Operation::IncMean,
                "min-max" => Operation::MinMax,
                "none" | _ => Operation::None,
            },
        };
        let sleep = args
            .get("sleep")
            .cloned()
            .unwrap_or(String::from("0"))
            .parse::<u64>()
            .unwrap_or(0);

        // Sleep, if needed.
        let sleep = time::Duration::from_millis(sleep);
        thread::sleep(sleep);

        // Retrieve the state.
        let bucket = store::open("default").map_err(|e| {
            ErrorCode::InternalError(Some(format!("failed to open KV bucket: {e:?}")))
        })?;

        let data = bucket.get(&name).map_err(|e| {
            ErrorCode::InternalError(Some(format!("failed to retrieve from key '{name}': {e:?}")))
        })?;

        let mut vector = if let Some(data) = data {
            let vector: Vec<f32> = data
                .chunks_exact(4)
                .map(TryInto::try_into)
                .map(Result::unwrap)
                .map(f32::from_be_bytes)
                .collect();
            if vector.len() == size {
                vector
            } else {
                rand_vector(size)
            }
        } else {
            rand_vector(size)
        };

        // Update the state.
        let (val1, val2) = match operation {
            Operation::None => (None, None),
            Operation::Increment => {
                for elem in vector.iter_mut() {
                    *elem += 1.0_f32;
                }
                (None, None)
            }
            Operation::Sin => {
                for elem in vector.iter_mut() {
                    *elem += elem.sin();
                }
                (None, None)
            }
            Operation::IncMean => {
                let mean = vector.iter().sum::<f32>() / vector.len() as f32;
                for elem in vector.iter_mut() {
                    *elem += mean;
                }
                (Some(mean), None)
            }
            Operation::MinMax => (
                vector
                    .iter()
                    .min_by(|a, b| a.partial_cmp(b).unwrap())
                    .cloned(),
                vector
                    .iter()
                    .max_by(|a, b| a.partial_cmp(b).unwrap())
                    .cloned(),
            ),
        };

        // Save the state.
        let vec_bytes = vector
            .iter()
            .map(|x| x.to_be_bytes())
            .flatten()
            .collect::<Vec<u8>>();

        bucket.set(&name, &vec_bytes).map_err(|e| {
            ErrorCode::InternalError(Some(format!("failed to set to key '{name}': {e:?}")))
        })?;

        // Reply back to the client.
        info!("replying");
        Ok(http::Response::new(format!(
            "OK {name} {size} {operation:?} {sleep:?} {val1:?} {val2:?}\n"
        )))
    }
}
