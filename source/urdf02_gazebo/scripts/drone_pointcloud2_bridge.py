#!/usr/bin/env python3
"""Convert Gazebo's multi-line PointCloud into SlideSLAM PointCloud2 input."""

import rospy
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud, PointCloud2


class DronePointCloud2Bridge:
    def __init__(self):
        self.publisher = rospy.Publisher(
            "/os_cloud_node/points", PointCloud2, queue_size=3
        )
        rospy.Subscriber(
            "/drone/lidar/points_raw", PointCloud, self.convert, queue_size=3
        )

    def convert(self, message):
        # sensor_msgs.point_cloud2.create_cloud() needs a sized sequence.
        points = [(point.x, point.y, point.z) for point in message.points]
        cloud = point_cloud2.create_cloud_xyz32(message.header, points)
        self.publisher.publish(cloud)


if __name__ == "__main__":
    rospy.init_node("drone_pointcloud2_bridge")
    DronePointCloud2Bridge()
    rospy.spin()
