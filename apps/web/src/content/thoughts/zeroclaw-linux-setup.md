---
title: ZeroClaw Linux Setup.md
---
# Setting Up ZeroClaw on Linux

*February 21, 2026*

ZeroClaw is an ultra-lightweight, Rust-based AI agent runtime. It compiles to a single ~3.4MB binary, uses less than 5MB of RAM, and boots in under 10ms. Here's how to get it running on a home Linux machine.

---

## 1. Install Rust

ZeroClaw is built from source with Cargo. If you don't already have Rust installed:

```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

Verify with `rustc --version`.

## 2. Clone and Build ZeroClaw

```
git clone https://github.com/zeroclaw-labs/zeroclaw.git
cd zeroclaw
cargo build --release --locked
cargo install --path . --force --locked
```

> **Low-memory systems** (e.g. Raspberry Pi 3 with 1GB RAM): use `CARGO_BUILD_JOBS=1 cargo build --release` to avoid OOM.

After this, the `zeroclaw` binary is in your PATH.

## 3. Onboard / Configure

Run the interactive setup wizard:

```
zeroclaw onboard --interactive
```

Or do it non-interactively:

```
zeroclaw onboard --api-key YOUR_KEY --provider openrouter
```

### Using Ollama (fully local)

If you want to run everything locally with [Ollama](https://ollama.com):

1. Install Ollama and pull a model: `ollama pull llama3`
2. Make sure Ollama is serving: `ollama serve`
3. Onboard with: `zeroclaw onboard --api-key dummy --provider ollama`

ZeroClaw connects to Ollama at `localhost:11434` and ignores the API key.

## 4. Verify the Setup

```
zeroclaw status
zeroclaw doctor
```

`doctor` runs diagnostics and tells you if anything is misconfigured.

## 5. Start Using It

- **Single message:** `zeroclaw agent -m "Hello, ZeroClaw!"`
- **Interactive chat:** `zeroclaw agent`
- **Start the gateway** (HTTP API on port 3000): `zeroclaw gateway`
- **Full daemon mode:** `zeroclaw daemon`

## 6. Run as a systemd Service (Optional)

To keep ZeroClaw running in the background:

```
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/zeroclaw.service << 'EOF'
[Unit]
Description=ZeroClaw AI Agent Runtime

[Service]
ExecStart=%h/.cargo/bin/zeroclaw daemon
Restart=on-failure
Environment=ZEROCLAW_WORKSPACE=%h/zeroclaw-workspace

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now zeroclaw
```

Check logs with `journalctl --user -u zeroclaw -f`.

---

That's it. A single binary, minimal resources, and you're up and running.

- End of file -
