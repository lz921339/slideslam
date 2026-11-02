#include <algorithm>
#include <cmath>
#include <cstring>
#include <cstdio>
#include <limits>
#include <memory>
#include <string>

#include <boost/bind.hpp>
#include <gazebo/common/Events.hh>
#include <gazebo/gazebo.hh>
#include <gazebo/rendering/DepthCamera.hh>
#include <gazebo/sensors/DepthCameraSensor.hh>
#include <ros/ros.h>
#include <sensor_msgs/CameraInfo.h>
#include <sensor_msgs/Image.h>
#include <sensor_msgs/PointCloud2.h>
#include <sensor_msgs/image_encodings.h>
#include <sensor_msgs/point_cloud2_iterator.h>

namespace gazebo {

class SafeRgbdPlugin : public SensorPlugin {
 public:
  SafeRgbdPlugin() {
    std::fprintf(stderr, "[RGBD DEBUG] SafeRgbdPlugin constructor entered\n");
    std::fflush(stderr);
  }

  ~SafeRgbdPlugin() override {
    std::fprintf(stderr, "[RGBD DEBUG] SafeRgbdPlugin destructor entered\n");
    std::fflush(stderr);
  }

  void Load(sensors::SensorPtr sensor, sdf::ElementPtr sdf) override {
    std::fprintf(stderr, "[RGBD DEBUG] SafeRgbdPlugin::Load entered\n");
    std::fflush(stderr);
    gzmsg << "[RGBD DEBUG] SafeRgbdPlugin::Load entered\n";
    sensor_ = std::dynamic_pointer_cast<sensors::DepthCameraSensor>(sensor);
    if (!sensor_) {
      gzerr << "[RGBD DEBUG] SafeRgbdPlugin sensor cast failed\n";
      return;
    }
    gzmsg << "[RGBD DEBUG] DepthCameraSensor cast succeeded\n";

    camera_ = sensor_->DepthCamera();
    if (!camera_) {
      gzerr << "[RGBD DEBUG] Depth camera handle is null\n";
      return;
    }
    gzmsg << "[RGBD DEBUG] Depth camera handle acquired\n";
    if (!ros::isInitialized()) {
      gzerr << "[RGBD DEBUG] ROS is not initialized\n";
      return;
    }
    gzmsg << "[RGBD DEBUG] ROS is initialized\n";

    const std::string robot_namespace = Get(sdf, "robotNamespace", "");
    const std::string camera_name = Get(sdf, "cameraName", "camera");
    frame_name_ = Get(sdf, "frameName", "camera_link");
    min_range_ = GetDouble(sdf, "pointCloudCutoff", 0.08);
    max_range_ = GetDouble(sdf, "pointCloudCutoffMax", 10.0);

    node_.reset(new ros::NodeHandle(robot_namespace));
    image_pub_ = node_->advertise<sensor_msgs::Image>(
        Topic(camera_name, Get(sdf, "imageTopicName", "image_raw")), 1);
    image_info_pub_ = node_->advertise<sensor_msgs::CameraInfo>(
        Topic(camera_name, Get(sdf, "cameraInfoTopicName", "camera_info")), 1);
    depth_pub_ = node_->advertise<sensor_msgs::Image>(
        Topic(camera_name, Get(sdf, "depthImageTopicName", "depth/image_raw")), 1);
    depth_info_pub_ = node_->advertise<sensor_msgs::CameraInfo>(
        Topic(camera_name,
              Get(sdf, "depthImageCameraInfoTopicName", "depth/camera_info")),
        1);
    cloud_pub_ = node_->advertise<sensor_msgs::PointCloud2>(
        Topic(camera_name, Get(sdf, "pointCloudTopicName", "depth/points")), 1);
    gzmsg << "[RGBD DEBUG] ROS publishers created for camera '" << camera_name
        << "'\n";

    image_connection_ = camera_->ConnectNewImageFrame(boost::bind(
        &SafeRgbdPlugin::OnImage, this, _1, camera_->ImageWidth(),
        camera_->ImageHeight(), camera_->ImageDepth(), camera_->ImageFormat()));
    depth_connection_ = camera_->ConnectNewDepthFrame(boost::bind(
        &SafeRgbdPlugin::OnDepth, this, _1, camera_->ImageWidth(),
        camera_->ImageHeight(), 1u, std::string("FLOAT32")));

    sensor_->SetActive(true);
        gzmsg << "[RGBD DEBUG] SafeRgbdPlugin publishing camera '" << camera_name
          << "'\n";
  }

 private:
  static std::string Get(const sdf::ElementPtr &sdf, const std::string &name,
                         const std::string &fallback) {
    return sdf->HasElement(name) ? sdf->Get<std::string>(name) : fallback;
  }

  static double GetDouble(const sdf::ElementPtr &sdf, const std::string &name,
                          double fallback) {
    return sdf->HasElement(name) ? sdf->Get<double>(name) : fallback;
  }

  static std::string Topic(const std::string &camera,
                           const std::string &suffix) {
    if (!suffix.empty() && suffix.front() == '/') {
      return suffix;
    }
    if (camera.empty()) {
      return suffix;
    }
    return camera.back() == '/' ? camera + suffix : camera + "/" + suffix;
  }

  ros::Time Stamp() const {
    const common::Time time = sensor_->LastUpdateTime();
    return ros::Time(time.sec, time.nsec);
  }

  sensor_msgs::CameraInfo CameraInfo(unsigned int width, unsigned int height,
                                     const ros::Time &stamp) const {
    sensor_msgs::CameraInfo info;
    info.header.stamp = stamp;
    info.header.frame_id = frame_name_;
    info.width = width;
    info.height = height;

    const double fx = static_cast<double>(width) /
                      (2.0 * std::tan(camera_->HFOV().Radian() * 0.5));
    const double fy = fx;
    const double cx = (static_cast<double>(width) - 1.0) * 0.5;
    const double cy = (static_cast<double>(height) - 1.0) * 0.5;

    info.distortion_model = "plumb_bob";
    info.D.assign(5, 0.0);
    info.K[0] = fx;
    info.K[2] = cx;
    info.K[4] = fy;
    info.K[5] = cy;
    info.K[8] = 1.0;
    info.R[0] = 1.0;
    info.R[4] = 1.0;
    info.R[8] = 1.0;
    info.P[0] = fx;
    info.P[2] = cx;
    info.P[5] = fy;
    info.P[6] = cy;
    info.P[10] = 1.0;
    return info;
  }

  void OnImage(const unsigned char *data, unsigned int width,
               unsigned int height, unsigned int depth,
               const std::string & /*format*/) {
    if (image_pub_.getNumSubscribers() == 0 &&
        image_info_pub_.getNumSubscribers() == 0) {
      return;
    }

    sensor_msgs::Image image;
    image.header.stamp = Stamp();
    image.header.frame_id = frame_name_;
    image.width = width;
    image.height = height;
    image.is_bigendian = false;
    image.encoding = depth == 4 ? sensor_msgs::image_encodings::RGBA8
                                : sensor_msgs::image_encodings::RGB8;
    image.step = width * depth;
    image.data.resize(static_cast<size_t>(image.step) * height);
    std::memcpy(image.data.data(), data, image.data.size());
    image_pub_.publish(image);
    image_info_pub_.publish(CameraInfo(width, height, image.header.stamp));
  }

  void OnDepth(const float *data, unsigned int width, unsigned int height,
               unsigned int /*depth*/, const std::string & /*format*/) {
    const ros::Time stamp = Stamp();
    if (depth_pub_.getNumSubscribers() > 0 ||
        depth_info_pub_.getNumSubscribers() > 0) {
      sensor_msgs::Image image;
      image.header.stamp = stamp;
      image.header.frame_id = frame_name_;
      image.width = width;
      image.height = height;
      image.is_bigendian = false;
      image.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
      image.step = width * sizeof(float);
      image.data.resize(static_cast<size_t>(image.step) * height);
      std::memcpy(image.data.data(), data, image.data.size());
      depth_pub_.publish(image);
      depth_info_pub_.publish(CameraInfo(width, height, stamp));
    }

    if (cloud_pub_.getNumSubscribers() == 0) {
      return;
    }

    sensor_msgs::PointCloud2 cloud;
    cloud.header.stamp = stamp;
    cloud.header.frame_id = frame_name_;
    cloud.height = height;
    cloud.width = width;
    cloud.is_dense = false;
    sensor_msgs::PointCloud2Modifier modifier(cloud);
    modifier.setPointCloud2FieldsByString(1, "xyz");
    modifier.resize(static_cast<size_t>(width) * height);

    sensor_msgs::PointCloud2Iterator<float> out_x(cloud, "x");
    sensor_msgs::PointCloud2Iterator<float> out_y(cloud, "y");
    sensor_msgs::PointCloud2Iterator<float> out_z(cloud, "z");
    const double fx = static_cast<double>(width) /
                      (2.0 * std::tan(camera_->HFOV().Radian() * 0.5));
    const double fy = fx;
    const double cx = (static_cast<double>(width) - 1.0) * 0.5;
    const double cy = (static_cast<double>(height) - 1.0) * 0.5;
    const float nan = std::numeric_limits<float>::quiet_NaN();

    for (unsigned int v = 0; v < height; ++v) {
      for (unsigned int u = 0; u < width; ++u, ++out_x, ++out_y, ++out_z) {
        const float range = data[static_cast<size_t>(v) * width + u];
        if (!std::isfinite(range) || range < min_range_ || range > max_range_) {
          *out_x = nan;
          *out_y = nan;
          *out_z = nan;
          continue;
        }
        *out_x = static_cast<float>((static_cast<double>(u) - cx) * range / fx);
        *out_y = static_cast<float>((static_cast<double>(v) - cy) * range / fy);
        *out_z = range;
      }
    }
    cloud_pub_.publish(cloud);
  }

  sensors::DepthCameraSensorPtr sensor_;
  rendering::DepthCameraPtr camera_;
  std::unique_ptr<ros::NodeHandle> node_;
  ros::Publisher image_pub_;
  ros::Publisher image_info_pub_;
  ros::Publisher depth_pub_;
  ros::Publisher depth_info_pub_;
  ros::Publisher cloud_pub_;
  event::ConnectionPtr image_connection_;
  event::ConnectionPtr depth_connection_;
  std::string frame_name_;
  double min_range_ = 0.08;
  double max_range_ = 10.0;
};

GZ_REGISTER_SENSOR_PLUGIN(SafeRgbdPlugin)

}  // namespace gazebo
