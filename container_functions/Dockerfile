FROM ubuntu:22.04

COPY target/release/edgeless_container_function_d /edgeless_container_function_d

EXPOSE 7101

ENV RUST_LOG=info

CMD ["/edgeless_container_function_d", "--endpoint", "http://0.0.0.0:7101/"]
