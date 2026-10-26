#!/bin/sh
set -eu
# Run on a Linux Docker host with a native x64 bundle already built.
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
docker run --rm -v "$root/dist:/bundles:ro" ubuntu:26.04 /bin/sh -ec '
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libegl1 libgl1 libxkbcommon0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-xinerama0 >/dev/null
  cat /etc/os-release | head -2
  /bundles/auto-resume-agent/auto-resume-agent --version
  QT_QPA_PLATFORM=offscreen /bundles/AutoResumeAgent/AutoResumeAgent --smoke-test
  echo "Ubuntu 26.04 frozen CLI + Qt offscreen GUI: PASS"
'
