#!/usr/bin/env python3
"""Publish a repeatable 3D inspection trajectory on /robot1/cmd_vel."""

import rospy
from geometry_msgs.msg import Twist


class DroneTrajectory:
    PHASES = (
        (4.0, 0.40, 0.00, 0.00, 0.00),  # forward
        (4.0, 0.00, 0.30, 0.00, 0.00),  # lateral
        (3.0, 0.00, 0.00, 0.20, 0.00),  # climb
        (4.0, 0.00, 0.00, 0.00, 0.40),  # yaw
        (4.0, -0.40, 0.00, 0.00, 0.00),  # return forward
        (4.0, 0.00, -0.30, 0.00, 0.00),  # return lateral
        (3.0, 0.00, 0.00, -0.20, 0.00),  # descend
        (4.0, 0.00, 0.00, 0.00, -0.40),  # restore yaw
    )

    def __init__(self):
        topic = rospy.get_param("~cmd_vel_topic", "/robot1/cmd_vel")
        self.publisher = rospy.Publisher(topic, Twist, queue_size=5)
        self.rate = rospy.Rate(float(rospy.get_param("~rate", 30.0)))
        self.start_delay = float(rospy.get_param("~start_delay", 2.0))
        self.loop = bool(rospy.get_param("~loop", True))

    @staticmethod
    def _command(phase):
        _, x, y, z, yaw = phase
        message = Twist()
        message.linear.x = x
        message.linear.y = y
        message.linear.z = z
        message.angular.z = yaw
        return message

    def run(self):
        rospy.sleep(self.start_delay)
        while not rospy.is_shutdown():
            for phase in self.PHASES:
                deadline = rospy.Time.now() + rospy.Duration(phase[0])
                message = self._command(phase)
                while not rospy.is_shutdown() and rospy.Time.now() < deadline:
                    self.publisher.publish(message)
                    self.rate.sleep()
            if not self.loop:
                break
        self.publisher.publish(Twist())


if __name__ == "__main__":
    rospy.init_node("drone_trajectory")
    DroneTrajectory().run()
