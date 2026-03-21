#!/usr/bin/with-contenv bashio

bashio::log.info "============================================"
bashio::log.info "  GitHub Copilot Bridge Add-on Starting"
bashio::log.info "============================================"

# Read configuration
GITHUB_TOKEN=$(bashio::config 'github_token')
PORT=$(bashio::config 'port')

bashio::log.info "Configuration:"
bashio::log.info "  Port: ${PORT}"

if bashio::var.is_empty "${GITHUB_TOKEN}"; then
    bashio::log.fatal "No GitHub token configured. Please set 'github_token' in the add-on options."
    exit 1
fi
bashio::log.info "  GitHub token: [set]"

# Verify the Copilot CLI binary is present and log its version
bashio::log.info "Verifying Copilot CLI binary..."
if ! command -v copilot >/dev/null 2>&1; then
    bashio::log.fatal "Copilot CLI binary not found at /usr/local/bin/copilot. The image may be corrupted — try reinstalling the add-on."
    exit 1
fi

COPILOT_VERSION=$(copilot --version 2>&1 || true)
bashio::log.info "  Copilot CLI version: ${COPILOT_VERSION}"

# Authenticate the Copilot CLI using the token via environment variable.
# GH_TOKEN is picked up automatically by the CLI without interactive prompts.
export GH_TOKEN="${GITHUB_TOKEN}"
bashio::log.info "GH_TOKEN exported for CLI authentication."

# Check auth status (informational only — token-only auth may show as unverified here
# but will succeed at runtime via GH_TOKEN).
bashio::log.info "Checking Copilot CLI auth status (informational)..."
AUTH_OUTPUT=$(copilot -p "auth status" 2>&1)
AUTH_EXIT=$?
if [ "${AUTH_EXIT}" -eq 0 ]; then
    bashio::log.info "Auth status: OK"
else
    bashio::log.warning "Auth status check returned exit code ${AUTH_EXIT}. Output: ${AUTH_OUTPUT}"
    bashio::log.warning "This is expected when only GH_TOKEN is set without a persisted login session."
    bashio::log.warning "The ACP server will authenticate via GH_TOKEN at runtime."
fi

# Start the Copilot CLI in ACP server mode with a retry loop.
MAX_RETRIES=5
RETRY_DELAY=5
ATTEMPT=1

while true; do
    bashio::log.info "--------------------------------------------"
    bashio::log.info "Starting Copilot CLI in server mode on port ${PORT} (attempt ${ATTEMPT}/${MAX_RETRIES})..."
    bashio::log.info "Command: copilot --server --port ${PORT}"

    copilot --server --port "${PORT}" 2>&1 | while IFS= read -r line; do
        bashio::log.info "[copilot] ${line}"
    done
    EXIT_CODE=${PIPESTATUS[0]}

    bashio::log.info "Copilot CLI process exited with code ${EXIT_CODE}."

    if [ "${EXIT_CODE}" -eq 0 ]; then
        bashio::log.info "Copilot CLI ACP server exited normally. Stopping add-on."
        exit 0
    fi

    if [ "${ATTEMPT}" -ge "${MAX_RETRIES}" ]; then
        bashio::log.fatal "Copilot CLI ACP server failed after ${MAX_RETRIES} attempts (last exit code: ${EXIT_CODE}). Check the logs above for details."
        exit "${EXIT_CODE}"
    fi

    bashio::log.warning "Copilot CLI ACP server exited with code ${EXIT_CODE}. Retrying in ${RETRY_DELAY} seconds (attempt ${ATTEMPT}/${MAX_RETRIES})..."
    sleep "${RETRY_DELAY}"
    ATTEMPT=$((ATTEMPT + 1))
done
