#!/bin/bash
# Wrapper for pass-cli ssh-agent that supervises the agent process and
# guarantees keys are actually loaded before declaring success.
#
# pass-cli has two failure modes that bare KeepAlive doesn't catch:
#   1. The vault/items endpoint can flake at boot while `pass-cli test`
#      already succeeds -- pass-cli will then "start successfully" with
#      zero keys loaded, and stay that way until manually restarted.
#   2. A transient error on the long-poll events stream causes pass-cli
#      to voluntarily exit. KeepAlive respawns it, but the respawn can
#      itself hit failure (1).
#
# This wrapper starts pass-cli in the background, then verifies at least
# one key is reachable through the socket within KEY_LOAD_TIMEOUT. If
# not, it kills the agent and retries with exponential backoff. It only
# returns when the agent has been observed serving >=1 key, and waits on
# the agent forever after; if pass-cli ever exits, the outer loop kicks
# in again.

set -u

PASS_CLI=/opt/homebrew/bin/pass-cli
SSH_ADD=/usr/bin/ssh-add
SOCKET_PATH="$HOME/.ssh/proton-pass-agent.sock"

INITIAL_BACKOFF=5
MAX_BACKOFF=60
# pass-cli has an internal 30s refresh cycle. If the items endpoint is
# flaky (common after macOS wake), the first load returns 0 keys. We
# wait 90s so pass-cli gets 2-3 internal retries before we give up and
# kill it -- otherwise we kill pass-cli just as its own retry is about
# to succeed, and the outer loop hot-loops against a recovering API.
KEY_LOAD_TIMEOUT=90

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*"
}

network_ok() {
    "$PASS_CLI" test >/dev/null 2>&1
}

# Start pass-cli in the background, wait for it to bind the socket and
# load >=1 key, then wait on it forever. Returns non-zero if the agent
# never reached a healthy state or exited later.
start_and_supervise() {
    [ -e "$SOCKET_PATH" ] && rm -f "$SOCKET_PATH"

    log "starting pass-cli ssh-agent"
    "$PASS_CLI" ssh-agent start --socket-path "$SOCKET_PATH" &
    local pid=$!

    local deadline=$(($(date +%s) + KEY_LOAD_TIMEOUT))
    while [ "$(date +%s)" -lt "$deadline" ]; do
        if ! kill -0 "$pid" 2>/dev/null; then
            log "pass-cli exited during startup"
            wait "$pid" 2>/dev/null || true
            return 1
        fi
        if [ -S "$SOCKET_PATH" ]; then
            local keys
            keys=$(SSH_AUTH_SOCK="$SOCKET_PATH" "$SSH_ADD" -l 2>/dev/null | grep -c .)
            if [ "${keys:-0}" -ge 1 ]; then
                log "agent ready: $keys key(s) loaded; pid=$pid"
                wait "$pid"
                local rc=$?
                log "pass-cli exited (rc=$rc) after healthy start"
                # Signal "was healthy at some point" so outer loop can
                # reset backoff. rc is captured in the log above.
                return 0
            fi
        fi
        sleep 1
    done

    log "agent loaded 0 keys after ${KEY_LOAD_TIMEOUT}s; killing pid=$pid"
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    return 1
}

trap 'log "received signal; exiting"; exit 0' INT TERM

backoff=$INITIAL_BACKOFF
while true; do
    until network_ok; do
        log "waiting for Proton Pass connectivity (next probe in ${backoff}s)"
        t_before=$(date +%s)
        sleep "$backoff"
        elapsed=$(($(date +%s) - t_before))
        # macOS suspends the sleep call during system sleep, so wall
        # clock can jump far beyond the requested duration. Treat any
        # gross overshoot as "we just woke up": reset backoff and give
        # the network a moment to come up before the next probe.
        if [ "$elapsed" -gt $((backoff + 30)) ]; then
            log "detected system wake (slept ${elapsed}s, expected ${backoff}s); resetting backoff"
            backoff=$INITIAL_BACKOFF
            sleep 5
        else
            backoff=$((backoff * 2))
            [ "$backoff" -gt "$MAX_BACKOFF" ] && backoff=$MAX_BACKOFF
        fi
    done

    log "Proton Pass reachable; bringing up agent"

    # Only reset backoff when the agent actually reached a healthy state.
    # Without this guard, repeated Mode B failures (0-keys loads during
    # an items-endpoint outage) hot-loop every ~95s instead of backing
    # off, hammering the upstream API for hours.
    if start_and_supervise; then
        backoff=$INITIAL_BACKOFF
    fi

    log "retry in ${backoff}s"
    sleep "$backoff"
    backoff=$((backoff * 2))
    [ "$backoff" -gt "$MAX_BACKOFF" ] && backoff=$MAX_BACKOFF
done
