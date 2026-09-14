#!/bin/bash
# 04-install-packages.sh — First-boot package installation for Nabla Edge
#
# This script runs once during first boot of a freshly imaged Pi.
# It installs nabla-edge via APT (preferred) or falls back to local .deb/tarball.
#
# Order of preference:
#   1. APT install from coco.nabla.net (requires network)
#   2. Local .deb on boot partition
#   3. Local tarball on boot partition (legacy)
#
set -euo pipefail

LOG="/var/log/nabla-firstboot.log"
NABLA_LIST="/etc/apt/sources.list.d/nabla.list"
NABLA_LIST_CONTENT="deb [trusted=yes] https://coco.nabla.net/apt/ stable main"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

install_apt_source() {
  log "Installing APT source: $NABLA_LIST"
  echo "$NABLA_LIST_CONTENT" > "$NABLA_LIST"
  chmod 644 "$NABLA_LIST"
}

try_apt_install() {
  log "Attempting APT install..."
  
  if ! ping -c1 -W5 coco.nabla.net &>/dev/null; then
    log "Network not available (coco.nabla.net unreachable)"
    return 1
  fi
  
  install_apt_source
  
  if apt-get update -qq && apt-get install -y nabla-edge; then
    log "APT install successful"
    return 0
  else
    log "APT install failed"
    return 1
  fi
}

try_local_deb() {
  local deb
  deb="$(find /boot /boot/firmware -maxdepth 1 -name 'nabla-edge*.deb' 2>/dev/null | head -1)"
  
  if [ -z "$deb" ]; then
    log "No local .deb found"
    return 1
  fi
  
  log "Installing from local .deb: $deb"
  if dpkg -i "$deb"; then
    install_apt_source
    log "Local .deb install successful"
    return 0
  else
    log "Local .deb install failed"
    return 1
  fi
}

try_local_tarball() {
  local tarball tar_dir
  tarball="$(find /boot /boot/firmware -maxdepth 1 -name 'nabla-edge*.tar.gz' 2>/dev/null | head -1)"
  
  if [ -z "$tarball" ]; then
    log "No local tarball found"
    return 1
  fi
  
  log "Installing from tarball: $tarball"
  tar_dir="$(mktemp -d)"
  
  if tar xzf "$tarball" -C "$tar_dir"; then
    cd "$tar_dir/nabla-edge" 2>/dev/null || cd "$tar_dir"
    if [ -x "./install.sh" ]; then
      if ./install.sh; then
        log "Tarball install successful"
        rm -rf "$tar_dir"
        return 0
      fi
    fi
  fi
  
  log "Tarball install failed"
  rm -rf "$tar_dir"
  return 1
}

# --- Main ---

log "=== Nabla Edge first-boot package installation ==="

# Always ensure apt source is installed (even if package install fails)
install_apt_source

# Try install methods in order of preference
if try_apt_install; then
  log "Installation complete (APT)"
  exit 0
fi

if try_local_deb; then
  log "Installation complete (local .deb)"
  exit 0
fi

if try_local_tarball; then
  log "Installation complete (tarball)"
  exit 0
fi

log "ERROR: No install source available"
log "APT source installed — manual install: apt update && apt install nabla-edge"
exit 1
