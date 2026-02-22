FROM rust:1.93-slim AS builder

RUN apt-get update && apt-get install -y pkg-config ca-certificates git && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN git clone --depth 1 https://github.com/zeroclaw-labs/zeroclaw.git . \
    && cargo build --release --locked \
    && strip target/release/zeroclaw

RUN mkdir -p /data/workspace && \
    printf 'default_provider = "openrouter"\ndefault_model = "anthropic/claude-sonnet-4-20250514"\ndefault_temperature = 0.7\n\n[gateway]\nhost = "0.0.0.0"\nport = 3001\nallow_public_bind = true\n' > /data/config.toml && \
    chmod 600 /data/config.toml && \
    chown -R 65534:65534 /data

# --- Caddy binary ---
FROM caddy:2 AS caddy

# --- Production runtime ---
FROM debian:trixie-slim AS runtime

RUN apt-get update && apt-get install -y ca-certificates curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/target/release/zeroclaw /usr/local/bin/zeroclaw
COPY --from=caddy /usr/bin/caddy /usr/local/bin/caddy
COPY --from=builder --chown=65534:65534 /data /data

# Caddy config
COPY apps/zeroclaw/Caddyfile /etc/caddy/Caddyfile
COPY apps/zeroclaw/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

ENV ZEROCLAW_CONFIG_DIR=/data
ENV ZEROCLAW_GATEWAY_HOST=0.0.0.0
ENV ZEROCLAW_GATEWAY_PORT=3001
ENV ZEROCLAW_ALLOW_PUBLIC_BIND=true

USER 65534:65534

ENTRYPOINT ["/usr/local/bin/start.sh"]
