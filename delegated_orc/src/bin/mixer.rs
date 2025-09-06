// SPDX-FileCopyrightText: © 2025 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use clap::Parser;

#[derive(Debug, clap::Parser)]
#[command(long_about = "Randomly migrates function instances across nodes")]
struct Args {
    /// URL of the controller
    #[arg(short, long, default_value_t = String::from("http://127.0.0.1:7001"))]
    controller_url: String,
    /// Proxy type.
    #[arg(long, default_value_t = String::from("Redis"))]
    proxy_type: String,
    /// Redis URL (with proxy_type == Redis).
    #[arg(short, long, default_value_t = String::from("redis://localhost:6379"))]
    redis_url: String,
    /// Migration period, in ms
    #[arg(short, long, default_value_t = 1000)]
    period: u64,
    /// Experiment duration, in s.
    #[arg(short, long, default_value_t = 60)]
    duration: u64,
    /// Name of the function instance to be migrated.
    #[arg(short, long, default_value_t = String::from("noop"))]
    function: String,
    /// Only migrate across nodes matching this label, if specified.
    #[arg(short, long, default_value_t = String::default())]
    label: String,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    env_logger::init();

    let args = Args::parse();

    anyhow::ensure!(
        args.proxy_type.to_lowercase() == "redis",
        "unknown proxy type: {}",
        args.proxy_type
    );

    let mut mixer = delegated_orc::mixer::Mixer::new(
        &args.controller_url,
        &args.redis_url,
        &args.function,
        &args.label,
    )
    .await?;

    let start_time = std::time::Instant::now();
    loop {
        let migration_time = std::time::Instant::now();
        let num_migrations = mixer.mix().await;
        println!(
            "time {}, {} migrations, took {} ms",
            start_time.elapsed().as_secs_f32(),
            num_migrations,
            migration_time.elapsed().as_millis()
        );
        if start_time.elapsed().as_secs() >= args.duration {
            return Ok(());
        }

        std::thread::sleep(std::time::Duration::from_millis(args.period));
    }
}
