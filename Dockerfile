# Stage 1: Build the scalable-cli binary from source
FROM rust:alpine AS builder
RUN apk add --no-cache git musl-dev

WORKDIR /build
RUN git clone https://github.com/ScalableCapital/scalable-cli.git .
RUN cargo build --locked --release --features channel-prod --bin sc

# Stage 2: Runtime image
FROM alpine:3.19
RUN apk add --no-cache ca-certificates tzdata

# Copy the compiled binary from the builder stage
COPY --from=builder /build/target/release/sc /usr/local/bin/sc

# Create config directory and force file-based storage backend (disables D-Bus keyring requirement)
RUN mkdir -p /root/.config/scalable-cli && \
    echo '[auth]' > /root/.config/scalable-cli/config.toml && \
    echo 'session_backend = "file"' >> /root/.config/scalable-cli/config.toml

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /workspace
ENTRYPOINT ["/entrypoint.sh"]