# PX4 SITL integration

This package has two independent entry points:

- `car.copy.launch`: original car plus simplified drone demo.
- `px4_full.launch`: PX4 SITL/MAVROS/Gazebo plus the car in one world.

## Prerequisites

Install `mavros`, `mavros_msgs`, `gazebo_ros`, and `gazebo_plugins`, then build
PX4 SITL successfully before building this catkin workspace.

After copying this workspace to Ubuntu, initialize and build it:

```bash
cd /home/huo/-/demo05_ws
source /opt/ros/noetic/setup.bash
catkin_init_workspace src
chmod +x src/urdf02_gazebo/scripts/*.py
catkin_make
```

Configure the environment in every new terminal:

```bash
source /opt/ros/noetic/setup.bash
source ~/PX4-Autopilot/Tools/setup_gazebo.bash \
  ~/PX4-Autopilot ~/PX4-Autopilot/build/px4_sitl_default
export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:$HOME/PX4-Autopilot
export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:$HOME/PX4-Autopilot/Tools/sitl_gazebo
source /home/huo/-/demo05_ws/devel/setup.bash
```

## Start without automatic arming

```bash
roslaunch urdf02_gazebo px4_full.launch
```

The Offboard node publishes setpoints continuously but does not arm PX4.

## Start, enter OFFBOARD, and arm

Only run this in simulation:

```bash
roslaunch urdf02_gazebo px4_full.launch \
  auto_arm:=true target_x:=0 target_y:=0 target_z:=2
```

Change the target while running:

```bash
rostopic pub -1 /px4/command/pose geometry_msgs/PoseStamped \
"header: {frame_id: 'map'}
pose:
  position: {x: 3.0, y: 0.0, z: 2.0}
  orientation: {w: 1.0}"
```

Land:

```bash
rosservice call /mavros/set_mode "base_mode: 0
custom_mode: 'AUTO.LAND'"
```

## Communication topics

- Car odometry input: `/odom`
- PX4 odometry input: `/mavros/local_position/odom`
- Car to drone: `/communication/car_to_drone`
- Drone to car: `/communication/drone_to_car`
- Link status: `/communication/status`

## PX4 sensor model note

The original `drone.urdf.xacro` is not a PX4 aircraft and is not spawned by
`px4_full.launch`. The PX4 aircraft is the `iris` SDF model from
`PX4-Autopilot/Tools/sitl_gazebo/models`.

To retain the drone 3D lidar and RGB-D camera, make a copy of PX4's `iris`
model named `iris_slideslam`, then move the sensor link, fixed joint, ray sensor,
and OpenNI camera plugin definitions from `urdf/drone.urdf.xacro` into that SDF.
Keep these ROS interfaces:

- `/drone/lidar/points_raw`
- `/os_cloud_node/points`
- `/quadrotor/image`
- `/quadrotor/camera_info`
- `/quadrotor/depth/image_raw`
- `/quadrotor/depth/points`

The `drone_pointcloud2_bridge.py` node converts the Gazebo block-laser
`sensor_msgs/PointCloud` stream into the SlideSLAM-compatible
`sensor_msgs/PointCloud2` stream `/os_cloud_node/points`.
