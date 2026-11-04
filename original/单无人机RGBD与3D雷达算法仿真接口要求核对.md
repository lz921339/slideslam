# 单无人机 RGB-D 与 3D 激光雷达联调 Topic 要求

当前阶段只联调一架同时搭载 RGB-D 相机和 3D 激光雷达的无人机，统一使用 `robot1` 命名空间。请仿真侧发布同步的 RGB 图像、与 RGB 对齐的深度图、相机内参、3D 点云、无人机 6DoF 里程计、仿真时钟以及完整 TF。RGB 和深度建议为 10 Hz，时间差不超过 0.02 秒；图像、点云与里程计时间差建议不超过 0.05 秒。深度图建议使用 `32FC1`、单位为米；3D 点云使用 `sensor_msgs/PointCloud2`，至少包含 `x、y、z、intensity` 字段，建议为 10～15 Hz。请另行发布 `/robot1/ground_truth/odom` 作为真实位姿，它只用于 ATE/RPE 精度评估，不能输入 SlideSLAM。配准点云、语义点云、语义观测、优化里程计、轨迹和地图等 Topic 由算法侧生成，仿真侧无需发布。测试场景请布置 `chair`、`table`、`tv/monitor` 等 RGB-D 模型支持的目标，以及车辆、树干或灯杆等 3D 雷达模型支持的目标，并提供包含前进、横移、变高度、偏航和返回已观测区域的飞行轨迹。
## 本次动态检查结果

检查环境：`slideslam-single-car:small-city-dev`（基于当前 `source/` 重建），服务器 X11/Gazebo GUI 链路，ROS Noetic。以下状态来自容器运行期间的实际 ROS 采样；只有完整满足本表契约且实际收到消息的接口才标记为已实现。

| Topic | 动态检查结果 | 状态 |
|---|---|---|
| `/clock` | `rosgraph_msgs/Clock`，仿真时间持续推进 | **已实现** |
| `/robot1/camera/color/image_raw` | 实测约 13.2 Hz；实际收到 `sensor_msgs/Image`，分辨率 `640×480`、编码 `rgb8`，`frame_id=robot1/camera_color_optical_frame` | **已实现** |
| `/robot1/camera/aligned_depth_to_color/image_raw` | 实测约 15.2 Hz；实际收到 `sensor_msgs/Image`，编码 `32FC1`，`frame_id=robot1/camera_color_optical_frame` | **已实现** |
| `/robot1/camera/color/camera_info` | 实测约 12.0 Hz；实际收到 `sensor_msgs/CameraInfo`，分辨率 `640×480`，发布内参 `fx=fy=381.3625`、`cx=319.5`、`cy=239.5`，`frame_id=robot1/camera_color_optical_frame` | **已实现** |
| `/robot1/lidar/points_v1` | 实测约 14.8 Hz，类型为 `sensor_msgs/PointCloud`；本轮仅作为 Gazebo 原始雷达内部话题，未作为要求中的 `/robot1/lidar/points_raw` 达标接口 | 未实现 |
| `/robot1/lidar/points_raw` | 实测约 14.7 Hz；实际收到 `sensor_msgs/PointCloud2`，`frame_id=robot1/lidar_link`，字段为 `x/y/z/intensity/ring/time`，桥接节点过滤非有限点 | **已实现** |
| `/robot1/lidar/cloud_registered_body` | 实测约 15.0 Hz；实际收到 `sensor_msgs/PointCloud2`，字段含 x/y/z/intensity，`frame_id=robot1/base_link` | **已实现** |
| `/robot1/odom` | 实测约 50 Hz；`header.frame_id=robot1/odom`，`child_frame_id=robot1/base_link` | **已实现** |
| `/robot1/ground_truth/odom` | 实测约 51.1 Hz；实际收到 `nav_msgs/Odometry`，`header.frame_id=world`，仅作为真值评估输出 | **已实现** |
| `/robot1/imu/data` | 实测约 237.5 Hz；实际收到 `sensor_msgs/Imu`，`frame_id=robot1/imu_link`，频率落在 100～400 Hz 要求内 | **已实现** |
| `/tf`、`/tf_static` | `/tf_static` 包含 `robot1/base_link` 到相机、光学坐标系、雷达和 IMU 的外参；动态 TF 仅观察到 `robot1/odom → robot1/base_link`（车辆自身的 `odom → base_footprint` 不属于 robot1），未再出现 `robot1/odom_2d` 或重复数据 | **已实现** |
| `/robot1/cmd_vel` | `geometry_msgs/Twist` 控制节点以 50 Hz 更新 Gazebo 模型；发布 `linear.x/y/z` 与 `angular.z` 后，位姿从 `(1.5, 0.0, 1.5)` 变为约 `(2.78, 1.35, 2.20)`，确认前进、横移、变高度和偏航控制生效；`drone_trajectory.py` 提供前进、横移、升降、偏航和返回段 | **已实现** |

补充核对：已在服务器 X11/Gazebo GUI 链路中进行两次各 20 s 的逐消息时间戳最近邻统计（每个消息与另一话题时间戳的最近值匹配）。第二次采样结果如下：

| 时间戳配对 | 样本数 | 平均差 | P95 | 最大差 | 50 ms 要求 |
|---|---:|---:|---:|---:|---|
| RGB-深度 | 102 | 0 ms | 0 ms | 0 ms | 满足 |
| RGB-点云 | 102 | 16.471 ms | 32 ms | 72 ms | 存在超限点 |
| RGB-里程计 | 102 | 4.588 ms | 8 ms | 116 ms | 存在超限点 |
| 深度-点云 | 102 | 16.471 ms | 32 ms | 72 ms | 存在超限点 |
| 深度-里程计 | 102 | 4.588 ms | 8 ms | 116 ms | 存在超限点 |
| 点云-里程计 | 151 | 5.060 ms | 8 ms | 44 ms | 满足 |

第一次采样的最大差分别为 RGB-深度 0 ms、RGB-点云 32 ms、RGB-里程计 20 ms、深度-点云 32 ms、深度-里程计 20 ms、点云-里程计 88 ms，说明仿真调度存在偶发抖动。当前 P95 均不超过 32 ms，但按“所有消息最大差不超过 50 ms”的严格标准，图像与点云/里程计的同步仍有超限样本，尚不能宣称整项完全满足。点云桥接节点已逐点过滤 `NaN/Inf`，但尚未完成独立的整帧有限值计数报告。


## 最小联调接口

| Topic | 发布方 | ROS 消息类型 | 建议频率 | 必需内容与要求 | 用途 |
|---|---|---|---:|---|---|
| `/clock` | Gazebo | `rosgraph_msgs/Clock` | 随仿真更新 | 所有传感器、里程计和 TF 使用同一仿真时间；设置 `/use_sim_time=true` | 统一时间基准 |
| `/robot1/camera/color/image_raw` | Gazebo | `sensor_msgs/Image` | 10 Hz | 建议 `640×480`；编码为 `bgr8` 或 `rgb8`；`frame_id=robot1/camera_color_optical_frame` | RGB 目标检测和实例分割 |
| `/robot1/camera/aligned_depth_to_color/image_raw` | Gazebo | `sensor_msgs/Image` | 10 Hz | 与 RGB 逐像素对齐且分辨率一致；建议 `32FC1`、单位为米；与 RGB 时间差不超过 `0.02 s` | 恢复目标三维位置和尺寸 |
| `/robot1/camera/color/camera_info` | Gazebo | `sensor_msgs/CameraInfo` | 与 RGB 同频 | 分辨率与 RGB 一致；提供正确的 `fx`、`fy`、`cx`、`cy` | 提供相机内参 |
| `/robot1/lidar/cloud_registered_body` | Gazebo或适配节点 | `sensor_msgs/PointCloud2` | 10～15 Hz | 点已转换到 `robot1/base_link`；至少包含 `x`、`y`、`z`、`intensity`；距离单位为米；无 `NaN/Inf`；`frame_id=robot1/base_link` | 绕过 LIO，直接验证激光语义前端 |
| `/robot1/odom` | Gazebo | `nav_msgs/Odometry` | 20～100 Hz | 完整 6DoF 位姿、四元数姿态、线速度和角速度；`header.frame_id=robot1/odom`；`child_frame_id=robot1/base_link`；与图像、点云时间差不超过 `0.05 s` | 最小联调中的 SlideSLAM 里程计输入 |
| `/robot1/ground_truth/odom` | Gazebo | `nav_msgs/Odometry` | 20～100 Hz | Gazebo 无噪声真实位姿；建议 `header.frame_id=world`；不得作为 SlideSLAM 输入 | ATE、RPE 精度评估 |
| `/tf` | Gazebo或统一 TF 节点 | `tf2_msgs/TFMessage` | 20～100 Hz | 发布动态变换 `robot1/odom → robot1/base_link`，并与 `/robot1/odom` 一致 | 坐标变换和 RViz 显示 |
| `/tf_static` | Gazebo或 `robot_state_publisher` | `tf2_msgs/TFMessage` | 启动时一次 | 发布机体到 RGB-D 相机和 3D 雷达的固定安装外参 | 传感器坐标变换 |
| `/robot1/cmd_vel` 或飞行设定值 Topic | 控制侧 | `geometry_msgs/Twist` 或双方约定类型 | 20～50 Hz | 支持三维平移和偏航；若 Gazebo 执行自动航线，可不提供外部控制 Topic | 控制无人机运动 |

## 完整联调接口

| Topic | 发布方 | ROS 消息类型 | 建议频率 | 必需内容与要求 | 用途 |
|---|---|---|---:|---|---|
| `/clock` | Gazebo | `rosgraph_msgs/Clock` | 随仿真更新 | 所有传感器、IMU、真值、LIO 和 TF 使用同一仿真时间；设置 `/use_sim_time=true` | 统一时间基准 |
| `/robot1/camera/color/image_raw` | Gazebo | `sensor_msgs/Image` | 10 Hz | 建议 `640×480`；编码为 `bgr8` 或 `rgb8`；`frame_id=robot1/camera_color_optical_frame` | RGB 目标检测和实例分割 |
| `/robot1/camera/aligned_depth_to_color/image_raw` | Gazebo | `sensor_msgs/Image` | 10 Hz | 与 RGB 逐像素对齐且分辨率一致；建议 `32FC1`、单位为米；与 RGB 时间差不超过 `0.02 s` | 恢复目标三维位置和尺寸 |
| `/robot1/camera/color/camera_info` | Gazebo | `sensor_msgs/CameraInfo` | 与 RGB 同频 | 分辨率与 RGB 一致；提供正确的 `fx`、`fy`、`cx`、`cy` | 提供相机内参 |
| `/robot1/lidar/points_raw` | Gazebo | `sensor_msgs/PointCloud2` | 10～20 Hz | 包含 `x`、`y`、`z`、`intensity`、`ring` 和点内相对时间 `time`；距离单位为米；无 `NaN/Inf`；`frame_id=robot1/lidar_link`；字段名称和单位与 LIO 适配器一致 | Faster-LIO 原始雷达输入 |
| `/robot1/imu/data` | Gazebo | `sensor_msgs/Imu` | 100～400 Hz | 提供角速度和线加速度；单位为 `rad/s`、`m/s²`；时间戳来自 `/clock`；`frame_id=robot1/imu_link` | Faster-LIO 原始 IMU 输入 |
| `/robot1/lio/odom` | Faster-LIO或等价 LIO | `nav_msgs/Odometry` | 20～100 Hz | 完整 6DoF 估计位姿和速度；不得直接复制 Gazebo 真值；可重映射为 SlideSLAM 使用的里程计 Topic | 完整链路中的 SlideSLAM 里程计输入 |
| `/robot1/lidar/cloud_registered_body` | Faster-LIO或点云配准节点 | `sensor_msgs/PointCloud2` | 10～20 Hz | 经过运动补偿和配准；转换到 `robot1/base_link`；至少包含 `x`、`y`、`z`、`intensity`；`frame_id=robot1/base_link` | 激光语义分割和目标建模输入 |
| `/robot1/ground_truth/odom` | Gazebo | `nav_msgs/Odometry` | 20～100 Hz | Gazebo 无噪声真实位姿；建议 `header.frame_id=world`；只能用于精度评估，不得输入 Faster-LIO 或 SlideSLAM | ATE、RPE 精度评估 |
| `/tf` | LIO或统一 TF 节点 | `tf2_msgs/TFMessage` | 20～100 Hz | 动态变换与 `/robot1/lio/odom` 一致；同一个 child frame 只能有一个父节点，禁止 Gazebo 真值与 LIO 重复发布同名动态 TF | 算法坐标变换和 RViz 显示 |
| `/tf_static` | Gazebo或 `robot_state_publisher` | `tf2_msgs/TFMessage` | 启动时一次 | 发布 `robot1/base_link → robot1/camera_link`、`robot1/base_link → robot1/lidar_link`、`robot1/base_link → robot1/imu_link` 及相机光学坐标系变换；外参与 Gazebo 模型一致 | RGB-D、雷达和 IMU 固定外参 |
| `/robot1/cmd_vel` 或飞行设定值 Topic | 控制侧 | `geometry_msgs/Twist` 或双方约定类型 | 20～50 Hz | 支持三维平移和偏航；若 Gazebo 执行自动航线，可不提供外部控制 Topic | 控制无人机运动 |

