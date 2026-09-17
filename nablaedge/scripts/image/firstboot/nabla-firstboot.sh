#!/bin/bash
# nabla-firstboot.sh — First-boot setup for Nabla Edge Pi
# Runs once on first boot, installs edge package, configures hostname/octeto
# Does NOT prompt for Wi-Fi or keyboard (those are baked at image write time)
set -euo pipefail

LOG="/var/log/nabla-firstboot.log"
FLAG_FILE="/boot/firmware/nabla-firstboot.flag"
[ -f "$FLAG_FILE" ] || FLAG_FILE="/boot/nabla-firstboot.flag"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

die() {
  log "ERROR: $*"
  exit 1
}

# Read config from flag file
read_config() {
  hostname=""
  octeto=""
  if [ -f "$FLAG_FILE" ]; then
    while IFS='=' read -r key value; do
      case "$key" in
        hostname) hostname="$value" ;;
        octeto) octeto="$value" ;;
      esac
    done < <(grep -v '^#' "$FLAG_FILE" | grep '=')
  fi
}

# Set hostname if provided
configure_hostname() {
  if [ -n "${hostname:-}" ]; then
    log "Setting hostname: $hostname"
    hostnamectl set-hostname "$hostname" 2>/dev/null || \
      echo "$hostname" > /etc/hostname
    sed -i "s/127.0.1.1.*/127.0.1.1\t$hostname/" /etc/hosts 2>/dev/null || true
  fi
}

# Store octeto for network config
configure_octeto() {
  if [ -n "${octeto:-}" ]; then
    log "Storing octeto: $octeto"
    mkdir -p /etc/nabla-net
    echo "octeto=$octeto" > /etc/nabla-net/octeto.conf
  fi
}

# Install nabla-edge package
install_edge() {
  local boot_tar="/boot/firmware/nabla-edge.tar.gz"
  [ -f "$boot_tar" ] || boot_tar="/boot/nabla-edge.tar.gz"

  # Try APT first (requires network)
  if ping -c1 -W3 coco.nabla.net &>/dev/null 2>&1; then
    log "Network available — trying APT install"
    if ! grep -q 'coco.nabla.net' /etc/apt/sources.list.d/*.list 2>/dev/null; then
      echo 'deb [trusted=yes] https://coco.nabla.net/apt/ stable main' > \
        /etc/apt/sources.list.d/nabla.list
    fi
    if apt-get update -qq && apt-get install -y nabla-edge; then
      log "Installed nabla-edge via APT"
      return 0
    fi
    log "APT install failed, falling back to tarball"
  fi

  # Fallback: local tarball
  if [ -f "$boot_tar" ]; then
    log "Installing from tarball: $boot_tar"
    local tmpdir
    tmpdir=$(mktemp -d)
    tar xzf "$boot_tar" -C "$tmpdir"
    if [ -f "$tmpdir/nabla-edge/install.sh" ]; then
      cd "$tmpdir/nabla-edge"
      ./install.sh
      log "Installed nabla-edge from tarball"
    elif [ -f "$tmpdir/install.sh" ]; then
      cd "$tmpdir"
      ./install.sh
      log "Installed nabla-edge from tarball"
    else
      die "Cannot find install.sh in tarball"
    fi
    rm -rf "$tmpdir"
    return 0
  fi

  die "No install source: APT failed and no tarball found"
}

# Cleanup: remove flag and disable service
cleanup() {
  log "First-boot complete — cleaning up"
  rm -f "$FLAG_FILE"
  rm -f /boot/nabla-edge.tar.gz /boot/firmware/nabla-edge.tar.gz 2>/dev/null || true
  systemctl disable nabla-firstboot.service 2>/dev/null || true
}

main() {
  log "=== Nabla First-Boot Starting ==="
  log "Wi-Fi and keyboard were configured at image write time"
  log "This first-boot does NOT prompt for Wi-Fi or keyboard"

  if [ ! -f "$FLAG_FILE" ]; then
    log "No flag file found — skipping (already ran?)"
    exit 0
  fi

  read_config
  configure_hostname
  configure_octeto
  install_edge
  cleanup

  log "=== Nabla First-Boot Complete ==="
  log "User will be prompted to create account on first login"
}

main "$@"
