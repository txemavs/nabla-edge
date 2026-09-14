#!/bin/bash
# install.sh — Install NablaEdge tools system-wide
# Usage: sudo ./install.sh [--uninstall]
#
# Installs nabla-config, nabla-image, and related tools to /usr/local/bin
# so they work with `sudo nabla-config` (root PATH includes /usr/local/bin).
set -euo pipefail

VERSION="0.1.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/usr/local/bin"
OPT_DIR="/opt/nabla-edge"

# Tools to install to /usr/local/bin
TOOLS=(
  nabla-config
  nabla-image
)

err() { echo "ERROR: $*" >&2; exit 1; }
log() { echo ":: $*"; }

need_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root." >&2
    echo "Usage: sudo $0" >&2
    exit 1
  fi
}

install_tools() {
  log "Installing NablaEdge tools to $INSTALL_DIR..."

  # Ensure install directory exists
  install -d -m 755 "$INSTALL_DIR"

  # Install each tool
  for tool in "${TOOLS[@]}"; do
    local src="$SCRIPT_DIR/scripts/$tool"
    local dst="$INSTALL_DIR/$tool"

    if [ -f "$src" ]; then
      log "  Installing $tool"
      install -m 755 "$src" "$dst"
    else
      echo "  WARNING: $src not found, skipping"
    fi
  done

  # Create /opt/nabla-edge structure for voice/accessories config
  log "Creating $OPT_DIR structure..."
  install -d -m 755 "$OPT_DIR"
  install -d -m 755 "$OPT_DIR/voice"

  # Copy voice installer if present
  if [ -f "$SCRIPT_DIR/voice/install-lva.sh" ]; then
    log "  Installing voice/install-lva.sh"
    install -m 755 "$SCRIPT_DIR/voice/install-lva.sh" "$OPT_DIR/voice/"
  fi

  # Copy voice config example if present
  if [ -f "$SCRIPT_DIR/voice/voice.conf.example" ]; then
    install -m 644 "$SCRIPT_DIR/voice/voice.conf.example" "$OPT_DIR/voice/"
  fi

  log "Installation complete."
  log ""
  log "Tools installed to $INSTALL_DIR:"
  for tool in "${TOOLS[@]}"; do
    if [ -x "$INSTALL_DIR/$tool" ]; then
      echo "  - $tool"
    fi
  done
  log ""
  log "You can now run:"
  log "  sudo nabla-config"
  log "  sudo nabla-image --help"
}

uninstall_tools() {
  log "Uninstalling NablaEdge tools from $INSTALL_DIR..."

  for tool in "${TOOLS[@]}"; do
    local dst="$INSTALL_DIR/$tool"
    if [ -f "$dst" ]; then
      log "  Removing $tool"
      rm -f "$dst"
    fi
  done

  log "Uninstall complete."
  log "Note: $OPT_DIR and /etc/nabla-edge were NOT removed (may contain user config)."
}

show_help() {
  cat <<EOF
NablaEdge Installer v$VERSION

Usage: sudo $0 [OPTIONS]

OPTIONS
    --uninstall     Remove tools from $INSTALL_DIR
    --help, -h      Show this help

DESCRIPTION
    Installs NablaEdge CLI tools (nabla-config, nabla-image) to $INSTALL_DIR
    so they are available system-wide, including when running with sudo.

    Root's PATH typically includes /usr/local/bin, so after installation:
        sudo nabla-config

    works without needing ~/bin in PATH.

FILES
    $INSTALL_DIR/nabla-config
    $INSTALL_DIR/nabla-image
    $OPT_DIR/voice/install-lva.sh

EOF
}

main() {
  case "${1:-}" in
    -h|--help|help)
      show_help
      ;;
    --uninstall|uninstall)
      need_root
      uninstall_tools
      ;;
    "")
      need_root
      install_tools
      ;;
    *)
      err "Unknown option: $1"
      ;;
  esac
}

main "$@"
