#!/bin/bash
# Wrapper for pass-cli ssh-agent that supervises the agent process and
# guarantees keys are actually loaded before declaring success.
#
# pass-cli has two failure modes that bare KeepAlive doesn't catch:
#   1. The vault/items endpoint can flake at boot while the session probe
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
#
# The reachability probe is an OPTIMISATION, never a gate. pass-cli's CLI
# surface moves under us: 2.2.4 (2026-07-31) removed the `test`
# subcommand this script used to probe with, and because a failed probe
# blocked the start, the agent silently never came up for four weeks. Any
# probe failure that looks like a CLI-surface change now fails OPEN and
# we attempt a start anyway. start_and_supervise's "socket serves >=1
# key" check is the real health check, and it depends on no other
# subcommand.

set -u

PASS_CLI=/opt/homebrew/bin/pass-cli
SSH_ADD=/usr/bin/ssh-add
SOCKET_PATH="$HOME/.ssh/proton-pass-agent.sock"
PID_FILE="$HOME/.ssh/proton-pass-agent.pid"
LOG_FILE="$HOME/Library/Logs/proton-pass-ssh-agent.log"

# Subcommand used to probe session + connectivity. Deliberately one that
# does NOT touch the macOS keyring: vault and item reads need the
# `ProtonPassCLI` keychain key and would pop an authorization dialog from
# a background agent. `info` reads session state only.
PROBE_CMD=info

INITIAL_BACKOFF=5
MAX_BACKOFF=60
# pass-cli has an internal 30s refresh cycle. If the items endpoint is
# flaky (common after macOS wake), the first load returns 0 keys. We
# wait 90s so pass-cli gets 2-3 internal retries before we give up and
# kill it -- otherwise we kill pass-cli just as its own retry is about
# to succeed, and the outer loop hot-loops against a recovering API.
KEY_LOAD_TIMEOUT=90
# A stuck probe used to write one line per minute forever (22k lines,
# 1.5MB). Log the first failure of a streak with its actual error text,
# then only every Nth repeat.
WAIT_LOG_EVERY=10
MAX_LOG_BYTES=$((5 * 1024 * 1024))

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*"
}

# Truncate the log in place once it gets large, keeping one generation.
# Must be copy-then-truncate, never mv: launchd holds our stdout open on
# this inode, so a renamed file would keep receiving every line we log.
rotate_log() {
    [ -f "$LOG_FILE" ] || return 0
    local size
    size=$(stat -f %z "$LOG_FILE" 2>/dev/null || echo 0)
    if [ "$size" -gt "$MAX_LOG_BYTES" ]; then
        cp -f "$LOG_FILE" "$LOG_FILE.1" 2>/dev/null || true
        : > "$LOG_FILE" 2>/dev/null || true
        log "rotated log at ${size} bytes (previous generation: $LOG_FILE.1)"
    fi
    return 0
}

preflight() {
    if [ ! -x "$PASS_CLI" ]; then
        log "ERROR: $PASS_CLI missing or not executable -- the agent cannot start until it is reinstalled (brew install protonpass/tap/pass-cli)"
        return 0
    fi
    log "pass-cli: $("$PASS_CLI" --version 2>&1 | head -1)"
    if "$PASS_CLI" "$PROBE_CMD" >/dev/null 2>&1; then
        log "probe '$PASS_CLI $PROBE_CMD' OK"
    else
        log "probe '$PASS_CLI $PROBE_CMD' non-zero at startup (see first waiting line for the reason)"
    fi
    return 0
}

# Set by probe_ok to the probe's output, for the caller to log.
PROBE_ERR=""
# Count of consecutive fail-open probes, for rate-limiting that log line.
PROBE_UNSUPPORTED=0

# Returns 0 when we should go ahead and (re)start the agent: either the
# probe succeeded, or the probe itself is unusable -- an unrecognised
# subcommand or a missing binary -- in which case we fail open rather
# than block the agent forever behind a broken check.
probe_ok() {
    local out rc
    out=$("$PASS_CLI" "$PROBE_CMD" 2>&1)
    rc=$?
    PROBE_ERR=$(printf '%s' "$out" | tr '\n' ' ' | cut -c1-200)
    [ "$rc" -eq 0 ] && return 0
    if [ "$rc" -eq 127 ] || printf '%s' "$out" | grep -qE 'unrecognized subcommand|unexpected argument'; then
        PROBE_UNSUPPORTED=$((PROBE_UNSUPPORTED + 1))
        if [ "$PROBE_UNSUPPORTED" -eq 1 ] || [ $((PROBE_UNSUPPORTED % WAIT_LOG_EVERY)) -eq 0 ]; then
            log "PROBE UNSUPPORTED ($("$PASS_CLI" --version 2>&1 | head -1)): ${PROBE_ERR:-exit $rc} -- failing open, starting the agent anyway"
        fi
        return 0
    fi
    return 1
}

# Kill any pass-cli agent bound to our socket that we did not start. A
# hand-run `pass-cli ssh-agent daemon start` leaves an orphan (ppid 1)
# holding the socket; starting a second agent on top of it leaves two
# processes fighting over one socket file, which surfaces as
# "Connection refused" from ssh-add. The supervisor is authoritative.
reap_orphan_agents() {
    local pids pid
    pids=$(pgrep -f "ssh-agent start --socket-path $SOCKET_PATH" 2>/dev/null)
    for pid in $pids; do
        log "reaping orphan pass-cli agent pid=$pid"
        kill "$pid" 2>/dev/null || true
    done
    if [ -n "$pids" ]; then
        sleep 1
    fi
    rm -f "$PID_FILE"
    return 0
}

# Start pass-cli in the background, wait for it to bind the socket and
# load >=1 key, then wait on it forever. Returns non-zero if the agent
# never reached a healthy state or exited later.
start_and_supervise() {
    reap_orphan_agents
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

rotate_log
preflight

backoff=$INITIAL_BACKOFF
probe_failures=0
while true; do
    until probe_ok; do
        probe_failures=$((probe_failures + 1))
        if [ "$probe_failures" -eq 1 ] || [ $((probe_failures % WAIT_LOG_EVERY)) -eq 0 ]; then
            log "waiting for Proton Pass connectivity (probe #${probe_failures} failed: ${PROBE_ERR:-no output}; next probe in ${backoff}s)"
        fi
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

    if [ "$probe_failures" -gt 0 ]; then
        log "Proton Pass reachable again after ${probe_failures} failed probe(s)"
        probe_failures=0
    fi
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
