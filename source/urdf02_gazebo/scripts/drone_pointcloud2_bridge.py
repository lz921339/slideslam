#!/usr/bin/env python3
"""Convert Gazebo's multi-line PointCloud into SlideSLAM PointCloud2 input."""

import rospy
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud, PointCloud2, PointField


class DronePointCloud2Bridge:
    def __init__(self):
        self.publisher = rospy.Publisher(
            "/robot1/lidar/cloud_registered_body", PointCloud2, queue_size=3
        )
        rospy.Subscriber(
            "/robot1/lidar/points_raw", PointCloud, self.convert, queue_size=3
        )

    def convert(self, message):
        # sensor_msgs.point_cloud2.create_cloud() needs a sized sequence.
        fields = [
            PointField("x", 0, PointField.FLOAT32, 1),
            PointField("y", 4, PointField.FLOAT32, 1),
            PointField("z", 8, PointField.FLOAT32, 1),
            PointField("intensity", 12, PointField.FLOAT32, 1),
        ]
        points = [
            (point.x, point.y, point.z, 1.0) for point in message.points
        ]
        cloud = point_cloud2.create_cloud(message.header, fields, points)
        self.publisher.publish(cloud)


if __name__ == "__main__":
    rospy.init_node("drone_pointcloud2_bridge")
    DronePointCloud2Bridge()
    rospy.spin()
