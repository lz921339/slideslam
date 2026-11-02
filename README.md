# SlideSLAM small-city baseline

This repository tracks the versioned control files for the `small-city` baseline:

- `slideslam-single-car-small-city/`: OCI layout metadata and manifests.
- `run-small-city-gui.sh`: GUI launcher for the server desktop.
- `run-small-city-wsl.sh`: WSL/Docker launcher.

The OCI layer data under `slideslam-single-car-small-city/blobs/` and the archive
`slideslam-single-car-small-city.tar` are intentionally excluded from Git because
the current artifact is about 7.9 GB and contains a single layer larger than the
GitHub file-size limit. Keep that artifact on the server at the documented path,
or publish it through an artifact/object-storage service separately.

## Baseline

The initial version is the server snapshot used on 2026-11-02. The launchers
expect the workspace at `/home/ubuntu20/workspace/slideslam` and the image
`slideslam-single-car:small-city-2026-10-29`.

## Local server checkout

```bash
cd /home/ubuntu20/workspace/slideslam
bash run-small-city-wsl.sh
```

For the GUI launcher, run `bash run-small-city-gui.sh` from a desktop session.
