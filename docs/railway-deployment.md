# Railway Deployment Runbook

Reference for deploying Docker services to Railway. Based on lessons learned deploying zeroclaw (Rust) and the Next.js web app.

## How Railway Works

Railway builds your Docker image, pushes it to its registry, starts the container, and runs a healthcheck. If the healthcheck passes, traffic is routed. If it fails, the deploy is rolled back.

**Key mental model:** Railway is a reverse proxy. It assigns a random port via the `PORT` env var and routes external traffic to it. Your service **must** listen on `$PORT`, not a hardcoded port.

## Common Gotchas

### 1. Port Binding — Use `$PORT`

Railway sets a `PORT` environment variable at runtime. Your service must listen on it. If you hardcode a port (e.g. 3000), Railway's proxy can't reach your service and healthchecks fail with "service unavailable" even though the container logs show the app is running fine.

**Fix:** Don't set a port in your Dockerfile or config. Let the app read `$PORT` from the environment.

```dockerfile
# BAD — overrides Railway's PORT
ENV MY_APP_PORT=3000

# GOOD — let Railway's PORT flow through
# (don't set any port env var; let your app read $PORT)
```

### 2. GLIBC Version Mismatch in Multi-Stage Builds

If your builder image uses a different Debian version than your runtime image, the binary will crash on startup with:

```
/lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.XX' not found
```

The container logs may not surface this clearly — you'll just see healthchecks failing.

**Common trap:** `rust:1.93-slim` is based on Debian **Trixie** (GLIBC 2.39), but `debian:bookworm-slim` only has GLIBC 2.36.

**Fix:** Match your runtime base image to your builder's Debian version:

```dockerfile
# Builder uses Trixie (default for rust:1.93-slim)
FROM rust:1.93-slim AS builder

# Runtime MUST also use Trixie
FROM debian:trixie-slim AS runtime   # NOT bookworm-slim
```

**Alternative:** Use `-bookworm` tags for both stages, or build a fully static binary with musl.

### 3. Config File Schema Validation

If your app uses a config file, make sure it matches the exact schema the app expects. A missing required field or wrong section name causes a parse error, crashing the app before it binds to any port.

**Symptom:** Healthchecks fail with "service unavailable", but the build succeeds. Check container logs for parse errors.

**Fix:** Find a test or example config in the source code — these are the ground truth for what's valid.

### 4. `railway.toml` — Config-as-Code

Railway looks for `railway.toml` in the repo root (or the path you configure). Key sections:

```toml
[build]
builder = "dockerfile"
dockerfilePath = "apps/myservice/Dockerfile"
watchPatterns = ["apps/myservice/**"]

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
numReplicas = 1
```

**In a monorepo:** Railway sees all Dockerfiles and `.toml` files during snapshot analysis. You'll see log lines like:

```
skipping 'Dockerfile' at 'apps/other/Dockerfile' as it is not rooted at a valid path
```

This is normal — Railway is noting files it found but isn't using for this service.

### 5. Healthcheck Debugging

Railway healthchecks hit `GET <healthcheckPath>` on the `$PORT` it assigned.

| Symptom | Likely Cause |
|---------|-------------|
| "service unavailable" from attempt #1 onward | App never bound to `$PORT` (wrong port, crash on startup, GLIBC mismatch) |
| First few attempts fail, then pass | Normal startup latency — increase `healthcheckTimeout` |
| All attempts fail after full retry window | App is crashing in a loop — check container logs |

**The healthcheck endpoint must:**
- Return HTTP 200
- Not require authentication (no bearer token, no pairing)
- Be fast (no heavy computation)

### 6. File Permissions in Docker

If your app warns about world-readable config files, `chmod 600` them during the build:

```dockerfile
RUN chmod 600 /data/config.toml
```

Make sure the `USER` directive matches the file ownership (`chown`).

## Dockerfile Template (Rust + Railway)

```dockerfile
FROM rust:1.93-slim AS builder

RUN apt-get update && apt-get install -y pkg-config ca-certificates git && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --depth 1 https://github.com/org/repo.git . \
    && cargo build --release --locked \
    && strip target/release/myapp

# Generate config at build time
RUN mkdir -p /data && \
    printf 'key = "value"\n' > /data/config.toml && \
    chmod 600 /data/config.toml && \
    chown -R 65534:65534 /data

# Runtime — MUST match builder's Debian version
FROM debian:trixie-slim AS runtime

RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/target/release/myapp /usr/local/bin/myapp
COPY --from=builder --chown=65534:65534 /data /data

# Do NOT set a port — let Railway's $PORT flow through
ENV MY_CONFIG_DIR=/data

USER 65534:65534

ENTRYPOINT ["myapp"]
CMD ["serve"]
```

## Debugging Checklist

When a Railway deploy fails healthchecks:

1. **Check container logs** — Is the app actually starting? Look for crash messages, parse errors, missing env vars.
2. **Check the port** — Is the app listening on `$PORT`? Not a hardcoded port?
3. **Check GLIBC** — Do your builder and runtime use the same Debian version?
4. **Check the healthcheck endpoint** — Does it return 200 without auth? Test locally with `curl`.
5. **Check config files** — Does the embedded config match the app's schema? Find test configs in the source.
