# Packages and apt (HTTP)

## What works today

Edge installs are still a **tarball** + `install.sh`, not yet `apt install`.

Public HTTP (via Droplet → Coco):

```text
https://coco.nabla.net/nabla.net/pkgs/nabla-edge.tar.gz
https://coco.nabla.net/nabla.net/packages/nabla-edge.tar.gz
```

Only paths `/nabla.net/` and `/apt/` are exposed. No basic auth.

Private share (operators): the same files live on the NAS `nabla.net` package folder; HTTP is the mirror for installs over the internet.

## Example fetch

```bash
curl -fsSL -o nabla-edge.tar.gz \
  https://coco.nabla.net/nabla.net/pkgs/nabla-edge.tar.gz
tar xzf nabla-edge.tar.gz
cd nabla-edge && sudo ./install.sh
```

## Apt (next)

`/apt/` is reserved for a future Debian repo (`dists/` + `pool/` + `.deb`). Metadata and publish scripts will live under repo `packages/` and `dist/`; heavy binaries stay on the HTTP mirror / Releases, not in git.

See also [`../../../packages/`](../../../packages/) and [`../../../dist/`](../../../dist/).
