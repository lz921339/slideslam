#!/usr/bin/env python3
"""Convert Gazebo's legacy PointCloud into raw and body-frame PointCloud2."""

import copy
import math

import rospy
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud, PointCloud2, PointField


class DronePointCloud2Bridge:
    def __init__(self):
        self.raw_frame = rospy.get_param("~raw_frame", "robot1/lidar_link")
        self.output_frame = rospy.get_param("~output_frame", "robot1/base_link")
        self.horizontal_samples = int(rospy.get_param("~horizontal_samples", 720))
        self.vertical_samples = int(rospy.get_param("~vertical_samples", 16))
        self.scan_rate = float(rospy.get_param("~scan_rate", 15.0))
        self.translation = (
            float(rospy.get_param("~lidar_to_base_x", 0.0)),
            float(rospy.get_param("~lidar_to_base_y", 0.0)),
            float(rospy.get_param("~lidar_to_base_z", -0.07)),
        )
        self.raw_publisher = rospy.Publisher(
            rospy.get_param("~raw_output_topic", "/robot1/lidar/points_raw"),
            PointCloud2,
            queue_size=3,
        )
        self.body_publisher = rospy.Publisher(
            rospy.get_param(
                "~output_topic", "/robot1/lidar/cloud_registered_body"
            ),
            PointCloud2,
            queue_size=3,
        )
        rospy.Subscriber(
            rospy.get_param("~input_topic", "/robot1/lidar/points_v1"),
            PointCloud,
            self.convert,
            queue_size=3,
        )

    @staticmethod
    def _channel_values(message, names):
        names = {name.lower() for name in names}
        for channel in message.channels:
            if channel.name.lower() in names and len(channel.values) == len(message.points):
                return channel.values
        return None

    def convert(self, message):
        body_fields = [
            PointField("x", 0, PointField.FLOAT32, 1),
            PointField("y", 4, PointField.FLOAT32, 1),
            PointField("z", 8, PointField.FLOAT32, 1),
            PointField("intensity", 12, PointField.FLOAT32, 1),
        ]
        raw_fields = body_fields + [
            PointField("ring", 16, PointField.UINT16, 1),
            PointField("time", 18, PointField.FLOAT32, 1),
        ]

        intensity_values = self._channel_values(message, ("intensity", "intensities"))
        ring_values = self._channel_values(message, ("ring", "laser_id"))
        time_values = self._channel_values(message, ("time", "timestamp"))
        tx, ty, tz = self.translation
        raw_points = []
        body_points = []
        for index, point in enumerate(message.points):
            x, y, z = point.x, point.y, point.z
            if not all(math.isfinite(value) for value in (x, y, z)):
                continue
            intensity = intensity_values[index] if intensity_values else 1.0
            if not math.isfinite(intensity):
                intensity = 0.0

            if ring_values:
                ring = max(0, min(self.vertical_samples - 1, int(ring_values[index])))
            else:
                ring = min(
                    self.vertical_samples - 1,
                    index // max(1, self.horizontal_samples),
                )
            if time_values:
                relative_time = float(time_values[index])
            else:
                horizontal_index = index % max(1, self.horizontal_samples)
                relative_time = horizontal_index / (
                    max(1.0, self.scan_rate) * max(1, self.horizontal_samples)
                )
            if not math.isfinite(relative_time):
                relative_time = 0.0

            raw_points.append((x, y, z, intensity, ring, relative_time))
            body_points.append((x + tx, y + ty, z + tz, intensity))

        header = copy.copy(message.header)
        header.frame_id = self.raw_frame
        raw_cloud = point_cloud2.create_cloud(header, raw_fields, raw_points)
        self.raw_publisher.publish(raw_cloud)

        header = copy.copy(message.header)
        header.frame_id = self.output_frame
        body_cloud = point_cloud2.create_cloud(header, body_fields, body_points)
        self.body_publisher.publish(body_cloud)


if __name__ == "__main__":
    rospy.init_node("drone_pointcloud2_bridge")
    DronePointCloud2Bridge()
    rospy.spin()
