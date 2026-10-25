#!/bin/sh
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/Applications" "$HOME/.local/share/auto-resume-agent" "$HOME/.local/bin"
ditto "$source_dir/AutoResumeAgent.app" "$HOME/Applications/AutoResumeAgent.app"
ditto "$source_dir/cli" "$HOME/.local/share/auto-resume-agent/cli"
chmod +x "$HOME/.local/share/auto-resume-agent/cli/auto-resume-agent"
ln -sfn "$HOME/.local/share/auto-resume-agent/cli/auto-resume-agent" "$HOME/.local/bin/auto-resume-agent"
printf '%s\n' "Installed in ~/Applications and ~/.local/bin."
