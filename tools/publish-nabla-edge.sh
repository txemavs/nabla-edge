#!/bin/bash
# publish-nabla-edge.sh — Build and publish Nabla Edge package
#
# Usage:
#   ./tools/publish-nabla-edge.sh [--dry-run] [--bump major|minor|patch] [--version X.Y.Z]
#
# Builds nabla-edge.deb and nabla-edge.tar.gz, then optionally copies to Coco.
# Without Coco access, produces artifacts in build/ for manual copying.
#
# Requirements:
#   - dpkg-deb (or fakeroot + dpkg)
#   - apt-ftparchive (from apt-utils, for apt index regeneration)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$REPO_ROOT/build"
PKG_STAGING="$BUILD_DIR/nabla-edge"
PKG_SRC="$REPO_ROOT/packages/nabla-edge"
SCRIPTS_SRC="$REPO_ROOT/nablaedge/scripts"
VOICE_SRC="$REPO_ROOT/nablaedge/voice"
FIRSTBOOT_SRC="$PKG_SRC/opt/nabla-edge/firstboot"

# Coco paths (SMB share or local mount)
COCO_APT="${COCO_APT:-}"               # e.g., /mnt/coco/apt or \\coco\nabla.net\apt
COCO_PACKAGES="${COCO_PACKAGES:-}"     # e.g., /mnt/coco/nabla.net/pkgs

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[publish]${NC} $*"; }
warn() { echo -e "${YELLOW}[publish]${NC} $*"; }
err()  { echo -e "${RED}[publish]${NC} $*" >&2; }
info() { echo -e "${BLUE}[publish]${NC} $*"; }

DRY_RUN=0
BUMP_TYPE=""
EXPLICIT_VERSION=""

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Build and publish Nabla Edge package (.deb + .tar.gz).

OPTIONS:
  --dry-run           Show what would be done without making changes
  --bump TYPE         Bump version: major, minor, or patch (default: patch)
  --version X.Y.Z     Set explicit version (overrides --bump)
  --help              Show this help

ENVIRONMENT:
  COCO_APT            Path to Coco apt repo (e.g., /mnt/coco/apt)
  COCO_PACKAGES       Path to Coco packages dir (e.g., /mnt/coco/nabla.net/pkgs)

Without COCO_* variables, artifacts are built in build/ for manual copying.

EXAMPLES:
  $(basename "$0")                      # Build with patch bump
  $(basename "$0") --bump minor         # Build with minor version bump
  $(basename "$0") --version 1.0.0      # Build with explicit version
  $(basename "$0") --dry-run            # Preview without building
EOF
  exit 0
}

# Parse current version from control file
get_current_version() {
  grep -E '^Version:' "$PKG_SRC/DEBIAN/control" | awk '{print $2}'
}

# Bump version: major.minor.patch
bump_version() {
  local current="$1" type="$2"
  local major minor patch
  IFS='.' read -r major minor patch <<< "$current"
  
  case "$type" in
    major) major=$((major + 1)); minor=0; patch=0 ;;
    minor) minor=$((minor + 1)); patch=0 ;;
    patch|*) patch=$((patch + 1)) ;;
  esac
  
  echo "${major}.${minor}.${patch}"
}

# Update version in control file
update_control_version() {
  local version="$1"
  sed -i "s/^Version:.*/Version: $version/" "$PKG_SRC/DEBIAN/control"
  log "Updated DEBIAN/control to version $version"
}

# Update version in nabla-config script
update_script_version() {
  local version="$1"
  if [ -f "$SCRIPTS_SRC/nabla-config" ]; then
    sed -i "s/^VERSION=.*/VERSION=\"$version\"/" "$SCRIPTS_SRC/nabla-config"
    log "Updated nabla-config VERSION to $version"
  fi
}

# Build the .deb package
build_deb() {
  local version="$1"
  local deb_file="nabla-edge_${version}_all.deb"
  
  log "Building .deb package..."
  
  # Clean and create staging directory
  rm -rf "$PKG_STAGING"
  mkdir -p "$PKG_STAGING"
  
  # Copy DEBIAN control files
  cp -r "$PKG_SRC/DEBIAN" "$PKG_STAGING/"
  chmod 755 "$PKG_STAGING/DEBIAN/postinst" "$PKG_STAGING/DEBIAN/prerm" 2>/dev/null || true
  
  # Create directory structure
  mkdir -p "$PKG_STAGING/opt/nabla-edge/bin"
  mkdir -p "$PKG_STAGING/opt/nabla-edge/voice"
  mkdir -p "$PKG_STAGING/opt/nabla-edge/firstboot"
  mkdir -p "$PKG_STAGING/etc/apt/sources.list.d"
  mkdir -p "$PKG_STAGING/etc/nabla-edge"
  
  # Copy scripts
  if [ -f "$SCRIPTS_SRC/nabla-config" ]; then
    cp "$SCRIPTS_SRC/nabla-config" "$PKG_STAGING/opt/nabla-edge/bin/"
    chmod 755 "$PKG_STAGING/opt/nabla-edge/bin/nabla-config"
  fi
  
  # Copy voice installer
  if [ -f "$VOICE_SRC/install-lva.sh" ]; then
    cp "$VOICE_SRC/install-lva.sh" "$PKG_STAGING/opt/nabla-edge/voice/"
    chmod 755 "$PKG_STAGING/opt/nabla-edge/voice/install-lva.sh"
  fi
  
  # Copy firstboot scripts
  if [ -d "$FIRSTBOOT_SRC" ]; then
    cp -r "$FIRSTBOOT_SRC"/* "$PKG_STAGING/opt/nabla-edge/firstboot/" 2>/dev/null || true
    chmod 755 "$PKG_STAGING/opt/nabla-edge/firstboot"/*.sh 2>/dev/null || true
  fi
  
  # Copy apt source list
  cp "$PKG_SRC/etc/apt/sources.list.d/nabla.list" "$PKG_STAGING/etc/apt/sources.list.d/"
  
  # Create VERSION file
  echo "$version" > "$PKG_STAGING/opt/nabla-edge/VERSION"
  
  # Build .deb
  if [ "$DRY_RUN" -eq 1 ]; then
    info "[dry-run] Would build: $BUILD_DIR/$deb_file"
  else
    if command -v fakeroot &>/dev/null; then
      fakeroot dpkg-deb --build "$PKG_STAGING" "$BUILD_DIR/$deb_file"
    else
      dpkg-deb --build "$PKG_STAGING" "$BUILD_DIR/$deb_file"
    fi
    log "Built: $BUILD_DIR/$deb_file"
  fi
  
  echo "$deb_file"
}

# Build the .tar.gz tarball (legacy install method)
build_tarball() {
  local version="$1"
  local tarball="nabla-edge.tar.gz"
  local tarball_dated="nabla-edge_${version}.tar.gz"
  local tar_staging="$BUILD_DIR/nabla-edge-tar"
  
  log "Building tarball..."
  
  rm -rf "$tar_staging"
  mkdir -p "$tar_staging/nabla-edge"
  
  # Copy contents for tarball
  mkdir -p "$tar_staging/nabla-edge/bin"
  mkdir -p "$tar_staging/nabla-edge/voice"
  mkdir -p "$tar_staging/nabla-edge/firstboot"
  mkdir -p "$tar_staging/nabla-edge/etc"
  
  if [ -f "$SCRIPTS_SRC/nabla-config" ]; then
    cp "$SCRIPTS_SRC/nabla-config" "$tar_staging/nabla-edge/bin/"
  fi
  
  if [ -f "$VOICE_SRC/install-lva.sh" ]; then
    cp "$VOICE_SRC/install-lva.sh" "$tar_staging/nabla-edge/voice/"
  fi
  
  # Copy firstboot scripts
  if [ -d "$FIRSTBOOT_SRC" ]; then
    cp -r "$FIRSTBOOT_SRC"/* "$tar_staging/nabla-edge/firstboot/" 2>/dev/null || true
  fi
  
  # Copy apt source template
  cp "$PKG_SRC/etc/apt/sources.list.d/nabla.list" "$tar_staging/nabla-edge/etc/"
  
  # VERSION file
  echo "$version" > "$tar_staging/nabla-edge/VERSION"
  
  # Create install.sh for tarball
  cat > "$tar_staging/nabla-edge/install.sh" <<'INSTALL_EOF'
#!/bin/bash
# install.sh — Install Nabla Edge from tarball
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[nabla-edge] Installing from tarball..."

# Install binaries
install -d -m 755 /opt/nabla-edge/bin
install -d -m 755 /opt/nabla-edge/voice
install -d -m 755 /etc/nabla-edge
install -d -m 755 /etc/nabla-net

if [ -f "$SCRIPT_DIR/bin/nabla-config" ]; then
  install -m 755 "$SCRIPT_DIR/bin/nabla-config" /opt/nabla-edge/bin/
  ln -sf /opt/nabla-edge/bin/nabla-config /usr/local/bin/nabla-config
fi

if [ -f "$SCRIPT_DIR/voice/install-lva.sh" ]; then
  install -m 755 "$SCRIPT_DIR/voice/install-lva.sh" /opt/nabla-edge/voice/
fi

# Install VERSION
if [ -f "$SCRIPT_DIR/VERSION" ]; then
  cp "$SCRIPT_DIR/VERSION" /opt/nabla-edge/
fi

# Install apt source (enables future apt upgrades)
if [ -f "$SCRIPT_DIR/etc/nabla.list" ]; then
  install -m 644 "$SCRIPT_DIR/etc/nabla.list" /etc/apt/sources.list.d/nabla.list
  echo "[nabla-edge] APT source installed: /etc/apt/sources.list.d/nabla.list"
  echo "[nabla-edge] Future updates: sudo apt update && sudo apt upgrade nabla-edge"
fi

echo "[nabla-edge] Installation complete. Run: sudo nabla-config"
INSTALL_EOF
  chmod 755 "$tar_staging/nabla-edge/install.sh"
  
  if [ "$DRY_RUN" -eq 1 ]; then
    info "[dry-run] Would build: $BUILD_DIR/$tarball"
    info "[dry-run] Would build: $BUILD_DIR/$tarball_dated"
  else
    cd "$tar_staging"
    tar czf "$BUILD_DIR/$tarball" nabla-edge
    cp "$BUILD_DIR/$tarball" "$BUILD_DIR/$tarball_dated"
    log "Built: $BUILD_DIR/$tarball"
    log "Built: $BUILD_DIR/$tarball_dated"
  fi
}

# Regenerate apt repository indexes
regenerate_apt_indexes() {
  local apt_dir="$1"
  
  log "Regenerating apt repository indexes..."
  
  if ! command -v apt-ftparchive &>/dev/null; then
    warn "apt-ftparchive not found. Install apt-utils to regenerate indexes."
    warn "Manual regeneration required on target system."
    return 1
  fi
  
  if [ "$DRY_RUN" -eq 1 ]; then
    info "[dry-run] Would regenerate Packages/Release in $apt_dir"
    return 0
  fi
  
  # Ensure directory structure
  mkdir -p "$apt_dir/dists/stable/main/binary-arm64"
  mkdir -p "$apt_dir/dists/stable/main/binary-amd64"
  mkdir -p "$apt_dir/dists/stable/main/binary-all"
  mkdir -p "$apt_dir/pool/main/n/nabla-edge"
  
  cd "$apt_dir"
  
  # Generate Packages files
  apt-ftparchive packages pool/main > dists/stable/main/binary-arm64/Packages
  cp dists/stable/main/binary-arm64/Packages dists/stable/main/binary-amd64/Packages
  cp dists/stable/main/binary-arm64/Packages dists/stable/main/binary-all/Packages
  
  gzip -kf dists/stable/main/binary-arm64/Packages
  gzip -kf dists/stable/main/binary-amd64/Packages
  gzip -kf dists/stable/main/binary-all/Packages
  
  # Generate Release file
  apt-ftparchive release dists/stable > dists/stable/Release
  
  log "Apt indexes regenerated in $apt_dir"
}

# Copy to Coco (if accessible)
deploy_to_coco() {
  local version="$1"
  local deb_file="nabla-edge_${version}_all.deb"
  local tarball="nabla-edge.tar.gz"
  local tarball_dated="nabla-edge_${version}.tar.gz"
  
  if [ -z "$COCO_APT" ] || [ -z "$COCO_PACKAGES" ]; then
    warn "COCO_APT and COCO_PACKAGES not set. Artifacts in build/ for manual copy."
    echo ""
    echo "Manual copy targets:"
    echo "  .deb → COCO_APT/pool/main/n/nabla-edge/"
    echo "  .tar.gz → COCO_PACKAGES/"
    echo ""
    echo "After copying .deb, regenerate apt indexes:"
    echo "  cd /path/to/apt"
    echo "  apt-ftparchive packages pool/main > dists/stable/main/binary-arm64/Packages"
    echo "  gzip -k dists/stable/main/binary-arm64/Packages"
    echo "  apt-ftparchive release dists/stable > dists/stable/Release"
    return 0
  fi
  
  if [ ! -d "$COCO_APT" ]; then
    err "COCO_APT not accessible: $COCO_APT"
    return 1
  fi
  
  log "Deploying to Coco..."
  
  if [ "$DRY_RUN" -eq 1 ]; then
    info "[dry-run] Would copy $deb_file → $COCO_APT/pool/main/n/nabla-edge/"
    info "[dry-run] Would copy $tarball → $COCO_PACKAGES/"
    info "[dry-run] Would regenerate apt indexes"
  else
    # Copy .deb to apt pool
    mkdir -p "$COCO_APT/pool/main/n/nabla-edge"
    cp "$BUILD_DIR/$deb_file" "$COCO_APT/pool/main/n/nabla-edge/"
    log "Copied: $deb_file → $COCO_APT/pool/main/n/nabla-edge/"
    
    # Regenerate apt indexes
    regenerate_apt_indexes "$COCO_APT"
    
    # Copy tarball to packages
    if [ -d "$COCO_PACKAGES" ]; then
      cp "$BUILD_DIR/$tarball" "$COCO_PACKAGES/"
      cp "$BUILD_DIR/$tarball_dated" "$COCO_PACKAGES/"
      log "Copied: $tarball → $COCO_PACKAGES/"
    fi
  fi
}

# Print summary
print_summary() {
  local version="$1"
  echo ""
  echo "=========================================="
  echo "  Nabla Edge $version"
  echo "=========================================="
  echo ""
  echo "Build artifacts:"
  ls -lh "$BUILD_DIR"/*.deb "$BUILD_DIR"/*.tar.gz 2>/dev/null || true
  echo ""
  echo "Test install (local):"
  echo "  sudo dpkg -i $BUILD_DIR/nabla-edge_${version}_all.deb"
  echo ""
  echo "Test update (Pi with apt source):"
  echo "  sudo apt update && sudo apt install nabla-edge"
  echo ""
}

# --- Main ---

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --bump)
      BUMP_TYPE="$2"
      shift 2
      ;;
    --version)
      EXPLICIT_VERSION="$2"
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    *)
      err "Unknown option: $1"
      usage
      ;;
  esac
done

# Determine version
CURRENT_VERSION="$(get_current_version)"
if [ -n "$EXPLICIT_VERSION" ]; then
  NEW_VERSION="$EXPLICIT_VERSION"
elif [ -n "$BUMP_TYPE" ]; then
  NEW_VERSION="$(bump_version "$CURRENT_VERSION" "$BUMP_TYPE")"
else
  NEW_VERSION="$(bump_version "$CURRENT_VERSION" "patch")"
fi

log "Current version: $CURRENT_VERSION"
log "New version: $NEW_VERSION"

if [ "$DRY_RUN" -eq 1 ]; then
  info "[dry-run mode enabled]"
fi

# Create build directory
mkdir -p "$BUILD_DIR"

# Update versions in source files
if [ "$DRY_RUN" -eq 0 ]; then
  update_control_version "$NEW_VERSION"
  update_script_version "$NEW_VERSION"
fi

# Build artifacts
build_deb "$NEW_VERSION"
build_tarball "$NEW_VERSION"

# Deploy to Coco (if configured)
deploy_to_coco "$NEW_VERSION"

# Summary
if [ "$DRY_RUN" -eq 0 ]; then
  print_summary "$NEW_VERSION"
fi

log "Done."
