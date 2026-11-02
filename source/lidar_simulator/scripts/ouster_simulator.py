#!/usr/bin/env python3
import rospy
import numpy as np
from sensor_msgs.msg import PointCloud2, PointField
from geometry_msgs.msg import TransformStamped
import tf2_ros
import math

class OusterSimulator:
    def __init__(self):
        rospy.init_node('ouster_simulator')
        self.pub = rospy.Publisher('/os_cloud_node/points', PointCloud2, queue_size=10)
        self.br = tf2_ros.TransformBroadcaster()
        self.rate = rospy.Rate(10)
        
    def generate_ouster_points(self, num_lines=16, points_per_line=512):
        points = []
        h_angles = np.linspace(-math.pi, math.pi, points_per_line)
        v_angles = np.linspace(-15*math.pi/180, 15*math.pi/180, num_lines)
        
        for v in v_angles:
            for h in h_angles:
                r = np.random.uniform(2.0, 8.0)
                x = r * math.cos(v) * math.cos(h)
                y = r * math.cos(v) * math.sin(h)
                z = r * math.sin(v)
                points.append([x, y, z])
                
        for _ in range(500):
            x = np.random.uniform(-5, 5)
            y = np.random.uniform(-5, 5)
            z = -0.2 + np.random.normal(0, 0.02)
            points.append([x, y, z])
            
        return np.array(points, dtype=np.float32)
    
    def publish_tf(self):
        t = TransformStamped()
        t.header.stamp = rospy.Time.now()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'os_sensor'
        t.transform.translation.x = 0
        t.transform.translation.y = 0
        t.transform.translation.z = 0.35
        t.transform.rotation.w = 1.0
        self.br.sendTransform(t)
    
    def numpy_to_pointcloud2(self, points):
        msg = PointCloud2()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = 'os_sensor'
        msg.height = 1
        msg.width = len(points)
        msg.fields = [
            PointField('x', 0, PointField.FLOAT32, 1),
            PointField('y', 4, PointField.FLOAT32, 1),
            PointField('z', 8, PointField.FLOAT32, 1),
        ]
        msg.point_step = 12
        msg.row_step = msg.point_step * len(points)
        msg.is_bigendian = False
        msg.is_dense = True
        msg.data = points.tobytes()
        return msg
    
    def run(self):
        rospy.loginfo("Ouster Simulator started on /os_cloud_node/points")
        while not rospy.is_shutdown():
            self.publish_tf()
            points = self.generate_ouster_points()
            msg = self.numpy_to_pointcloud2(points)
            self.pub.publish(msg)
            self.rate.sleep()

if __name__ == '__main__':
    sim = OusterSimulator()
    sim.run()
