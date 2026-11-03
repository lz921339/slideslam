SlideSLAM small_city offline package

This package contains a Docker image archive with the small_city world, its model assets, and the SlideSLAM launch/RViz overlays embedded.

1. Keep Docker Desktop running and enable Ubuntu-22.04 under Settings > Resources > WSL Integration.
2. In Ubuntu, open this folder and start the simulation:

   cd /mnt/d/Documents/ChatGPT/work/small-city-setup/offline-package
   GAZEBO_GUI=true bash ./run-small-city-wsl.sh

The first run imports slideslam-single-car-small-city.tar into Docker. Later runs reuse that imported image. This machine uses CPU inference by default.

The archive is self-contained. It does not need the original F: drive package or external scene asset mounts.
