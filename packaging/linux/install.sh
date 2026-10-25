#!/bin/sh
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target="${XDG_DATA_HOME:-$HOME/.local/share}/auto-resume-agent"
mkdir -p "$target" "$HOME/.local/bin" "${XDG_DATA_HOME:-$HOME/.local/share}/applications"
cp -R "$source_dir/cli" "$source_dir/gui" "$source_dir/assets" "$target/"
chmod +x "$target/cli/auto-resume-agent" "$target/gui/AutoResumeAgent"
ln -sfn "$target/cli/auto-resume-agent" "$HOME/.local/bin/auto-resume-agent"
cat > "${XDG_DATA_HOME:-$HOME/.local/share}/applications/auto-resume-agent.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Auto Resume Agent
Comment=Codex usage monitor and session recovery
Exec="$target/gui/AutoResumeAgent"
Icon=$target/assets/icon.png
Terminal=false
Categories=Development;Utility;
EOF
printf '%s\n' "Installed to $target. Add ~/.local/bin to PATH if needed."
