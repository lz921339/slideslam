#!/usr/bin/env python3
"""Convert Gazebo's PointCloud into a body-frame PointCloud2 cloud."""

import copy
import math

import rospy
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud, PointCloud2, PointField


class DronePointCloud2Bridge:
    def __init__(self):
        self.output_frame = rospy.get_param("~output_frame", "robot1/base_link")
        self.translation = (
            float(rospy.get_param("~lidar_to_base_x", 0.0)),
            float(rospy.get_param("~lidar_to_base_y", 0.0)),
            float(rospy.get_param("~lidar_to_base_z", -0.07)),
        )
        self.publisher = rospy.Publisher(
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

    def convert(self, message):
        fields = [
            PointField("x", 0, PointField.FLOAT32, 1),
            PointField("y", 4, PointField.FLOAT32, 1),
            PointField("z", 8, PointField.FLOAT32, 1),
            PointField("intensity", 12, PointField.FLOAT32, 1),
        ]

        intensity_values = next(
            (
                channel.values
                for channel in message.channels
                if channel.name.lower() in ("intensity", "intensities")
                and len(channel.values) == len(message.points)
            ),
            None,
        )
        tx, ty, tz = self.translation
        points = []
        for index, point in enumerate(message.points):
            x, y, z = point.x + tx, point.y + ty, point.z + tz
            if not all(math.isfinite(value) for value in (x, y, z)):
                continue
            intensity = intensity_values[index] if intensity_values else 1.0
            points.append((x, y, z, intensity))

        header = copy.copy(message.header)
        header.frame_id = self.output_frame
        cloud = point_cloud2.create_cloud(header, fields, points)
        self.publisher.publish(cloud)


if __name__ == "__main__":
    rospy.init_node("drone_pointcloud2_bridge")
    DronePointCloud2Bridge()
    rospy.spin()
