FROM ghcr.io/home-assistant/amd64-base-debian:bookworm

RUN apt-get update && \
    apt-get install -y \
        # Add any required packages here
        && rm -rf /var/lib/apt/lists/*

ENV COPILOT_VERSION v0.0.418

# Add additional commands here if needed