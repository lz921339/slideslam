# SlideSLAM 项目维护说明

项目目录：`/home/ubuntu20/workspace/slideslam`

这份项目由两部分组成：

- `source/` 是可以修改和提交到 Git 的源码。
- Docker 镜像是源码编译后的运行环境，当前基线镜像为 `slideslam-single-car:small-city-2026-10-29`。

不要直接修改正在运行的容器。容器删除后，容器内的修改可能丢失。

## 一、目录说明

```text
slideslam/
├── source/                 # 项目源码，日常只修改这里
├── Dockerfile.small-city   # 用源码重新制作 Docker 镜像
├── build-small-city.sh     # 自动构建镜像
├── run-small-city-wsl.sh   # 命令行/WSL 运行
├── run-small-city-gui.sh   # 图形界面运行
├── slideslam-single-car-small-city/  # 原始 OCI 镜像归档
└── DEV_WORKFLOW.md         # 本说明
```

源码包主要位置：

```text
source/SLIDE_SLAM/          # SlideSLAM 算法
source/urdf02_gazebo/       # Gazebo、车辆、无人机和 launch 文件
source/faster-lio/          # Faster-LIO
source/lidar_simulator/     # 雷达仿真
source/slide_slam_gazebo/   # Gazebo 场景
source/ouster_decoder/      # Ouster 解码器
source/ouster_example/      # Ouster ROS 驱动和示例
```

## 二、日常修改源码

先进入项目目录，查看当前状态：

```bash
cd /home/ubuntu20/workspace/slideslam
git status
```

建议每项工作使用独立分支：

```bash
git switch -c feat/robot1-topic
```

修改 `source/` 中的代码、配置或 launch 文件。例如：

```bash
vim source/urdf02_gazebo/launch/px4_full.launch
```

确认修改内容后提交：

```bash
git diff -- source/urdf02_gazebo/launch/px4_full.launch
git add source/urdf02_gazebo/launch/px4_full.launch
git commit -m "fix: update robot1 launch topic"
```

不要使用 `git add .`，因为工作区还保留了历史交付目录和大型镜像文件。提交时只添加本次修改的文件。

## 三、重新制作 Docker 镜像

先确认基线镜像存在：

```bash
sudo docker images | grep slideslam-single-car
```

使用当前源码制作开发镜像：

```bash
cd /home/ubuntu20/workspace/slideslam
bash build-small-city.sh
```

默认生成 `slideslam-single-car:small-city-dev`。也可以明确指定版本标签：

```bash
SLIDESLAM_IMAGE=slideslam-single-car:small-city-v1 \
  bash build-small-city.sh
```

构建过程会把 `source/` 复制到镜像内的 `/opt/slideslam_docker_ws/src/`，然后执行 `catkin build`。构建成功后，源码改动才会进入新镜像。

`.dockerignore` 已配置好，构建时不会把 7.9G 的 OCI 归档、无关交付目录和临时文件发送给 Docker。

## 四、运行镜像

命令行或 WSL 环境运行：

```bash
cd /home/ubuntu20/workspace/slideslam
SLIDESLAM_IMAGE=slideslam-single-car:small-city-dev \
  bash run-small-city-wsl.sh
```

图形界面运行：

```bash
cd /home/ubuntu20/workspace/slideslam
SLIDESLAM_IMAGE=slideslam-single-car:small-city-dev \
  bash run-small-city-gui.sh
```

如果不设置 `SLIDESLAM_IMAGE`，两个脚本默认运行原始基线镜像 `slideslam-single-car:small-city-2026-10-29`。

## 五、检查新镜像

确认 ROS 包能被找到：

```bash
sudo docker run --rm --entrypoint /bin/bash \
  slideslam-single-car:small-city-dev \
  -lc 'source /opt/slideslam_docker_ws/devel/setup.bash && \
       rospack find urdf02_gazebo && rospack find faster_lio'
```

查看镜像 ID 和大小：

```bash
sudo docker image inspect slideslam-single-car:small-city-dev \
  --format 'id={{.Id}} size={{.Size}}'
```

启动仿真后，根据接口要求检查 Topic：

```bash
rostopic list | grep robot1
```

## 六、发布和回退

测试通过后给源码提交打版本标签：

```bash
git tag -a v1.1.0-robot1 -m "robot1 topic update"
git show v1.1.0-robot1 --stat
```

同时记录对应的 Docker 镜像标签和镜像 ID。回退时使用旧的源码标签和旧的镜像标签，不要覆盖原始基线镜像：

```bash
git switch --detach v1.0.0-source-baseline
SLIDESLAM_IMAGE=slideslam-single-car:small-city-2026-10-29 \
  bash run-small-city-wsl.sh
```

## 七、大文件说明

`slideslam-single-car-small-city.tar` 和 OCI `blobs/` 是运行制品，不是源码；它们不提交到普通 Git 历史。`yolov8x-seg.pt` 也是外部模型文件。源码仓库只保存清单、脚本和源码，镜像及模型应保留在服务器制品目录或单独的制品仓库。

## 八、推送到 GitHub

配置 GitHub PAT 或 SSH key 后，在项目目录执行：

```bash
git remote add origin https://github.com/lz921339/slideslam.git
git push -u origin main
git push origin --tags
```

组员后续从 `main` 创建分支，提交后通过 Pull Request 合并。
