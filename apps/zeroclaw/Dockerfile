FROM rust:1.93-slim AS builder

RUN apt-get update && apt-get install -y pkg-config ca-certificates git && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN git clone --depth 1 https://github.com/zeroclaw-labs/zeroclaw.git . \
    && cargo build --release --locked \
    && strip target/release/zeroclaw

RUN mkdir -p /data/workspace && \
    printf '[workspace]\npath = "/data/workspace"\n\n[provider]\nname = "openrouter"\ndefault_model = "anthropic/claude-sonnet-4-20250514"\n\n[gateway]\nhost = "0.0.0.0"\nport = 3000\n' > /data/config.toml && \
    chown -R 65534:65534 /data

# --- Production runtime ---
FROM debian:bookworm-slim AS runtime

RUN apt-get update && apt-get install -y ca-certificates curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/target/release/zeroclaw /usr/local/bin/zeroclaw
COPY --from=builder --chown=65534:65534 /data /data

ENV ZEROCLAW_WORKSPACE=/data/workspace
ENV ZEROCLAW_CONFIG=/data/config.toml
ENV ZEROCLAW_GATEWAY_PORT=3000

EXPOSE 3000

USER 65534:65534

ENTRYPOINT ["zeroclaw", "gateway"]
