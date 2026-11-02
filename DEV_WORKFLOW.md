# Docker 项目维护流程

## 1. 修改代码

只修改 `source/` 下的源码。例如：

```bash
cd /home/ubuntu20/workspace/slideslam
vim source/urdf02_gazebo/launch/single_car_full_stack.launch
```

## 2. 提交源码

```bash
git status
git add source/urdf02_gazebo/launch/single_car_full_stack.launch
git commit -m "fix: update small-city launch configuration"
```

## 3. 构建开发镜像

```bash
bash build-small-city.sh
```

默认生成 `slideslam-single-car:small-city-dev`。也可以指定版本：

```bash
SLIDESLAM_IMAGE=slideslam-single-car:small-city-v1 bash build-small-city.sh
```

## 4. 运行开发镜像

```bash
SLIDESLAM_IMAGE=slideslam-single-car:small-city-dev \
  bash run-small-city-wsl.sh
```

图形界面使用同一个 `SLIDESLAM_IMAGE` 环境变量运行 `run-small-city-gui.sh`。

## 5. 发布

确认启动和 Topic 检查通过后，再给源码提交打 Tag，并记录对应镜像名和 digest。
