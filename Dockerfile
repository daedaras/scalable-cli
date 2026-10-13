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

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /workspace
ENTRYPOINT ["/entrypoint.sh"]