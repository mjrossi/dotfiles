function ssh-agent-restart --description 'Cleanly restart the Proton Pass SSH agent via launchd'
    set -l uid (id -u)
    set -l label com.proton.pass-cli.ssh-agent
    launchctl kickstart -k "gui/$uid/$label"
    or begin
        echo "ssh-agent-restart: launchctl kickstart failed; is the agent loaded?" >&2
        return 1
    end
    echo "kicked $label; tail logs with: tail -f ~/Library/Logs/proton-pass-ssh-agent.log"
end
