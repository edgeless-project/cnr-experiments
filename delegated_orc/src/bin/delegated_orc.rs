// SPDX-FileCopyrightText: © 2024 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use clap::Parser;

#[derive(Debug, clap::Parser)]
#[command(long_about = None)]
struct Args {
    #[arg(short, long, default_value_t = String::from("Redis"))]
    proxy_type: String,
    #[arg(short, long, default_value_t = String::from("redis://localhost:6379"))]
    redis_url: String,
    #[arg(short, long, default_value_t = 5)]
    epoch: u64,
}

fn main() -> anyhow::Result<()> {
    env_logger::init();

    let args = Args::parse();

    anyhow::ensure!(
        args.proxy_type.to_lowercase() == "redis",
        "unknown proxy type: {}",
        args.proxy_type
    );

    let mut rebalancer = delegated_orc::rebalancer::Rebalancer::new(&args.redis_url)?;

    loop {
        let start_time = std::time::Instant::now();
        let (done, num_migrations) = rebalancer.rebalance();
        if done {
            println!(
                "{} migrations, rebalance time {} ms",
                num_migrations,
                start_time.elapsed().as_millis()
            );
        }

        std::thread::sleep(std::time::Duration::from_secs(args.epoch));
    }
}
