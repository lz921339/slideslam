#!/usr/bin/env python3
"""Publish PX4 Offboard position setpoints and optionally arm the vehicle."""

import rospy
from geometry_msgs.msg import PoseStamped, Twist
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, SetMode


class Px4OffboardControl:
    def __init__(self):
        self.state = State()
        self.auto_arm = rospy.get_param("~auto_arm", False)
        self.target = PoseStamped()
        self.target.header.frame_id = rospy.get_param("~frame_id", "map")
        self.target.pose.position.x = rospy.get_param("~target_x", 0.0)
        self.target.pose.position.y = rospy.get_param("~target_y", 0.0)
        self.target.pose.position.z = rospy.get_param("~target_z", 2.0)
        self.target.pose.orientation.w = 1.0
        self.velocity = Twist()
        self.last_velocity_command = rospy.Time(0)
        self.velocity_timeout = rospy.Duration(
            rospy.get_param("~velocity_timeout", 0.5)
        )

        self.publisher = rospy.Publisher(
            "/mavros/setpoint_position/local", PoseStamped, queue_size=10
        )
        rospy.Subscriber("/mavros/state", State, self.state_callback)
        rospy.Subscriber("/px4/command/pose", PoseStamped, self.command_callback)
        rospy.Subscriber("/px4/command/cmd_vel", Twist, self.velocity_callback)

    def state_callback(self, message):
        self.state = message

    def command_callback(self, message):
        self.target = message
        if not self.target.header.frame_id:
            self.target.header.frame_id = "map"

    def velocity_callback(self, message):
        self.velocity = message
        self.last_velocity_command = rospy.Time.now()

    def integrate_velocity(self, dt):
        if rospy.Time.now() - self.last_velocity_command > self.velocity_timeout:
            return
        self.target.pose.position.x += self.velocity.linear.x * dt
        self.target.pose.position.y += self.velocity.linear.y * dt
        self.target.pose.position.z = max(
            0.15, self.target.pose.position.z + self.velocity.linear.z * dt
        )

    def publish_target(self):
        self.target.header.stamp = rospy.Time.now()
        self.publisher.publish(self.target)

    def wait_for_connection(self):
        rate = rospy.Rate(20)
        while not rospy.is_shutdown() and not self.state.connected:
            self.publish_target()
            rospy.loginfo_throttle(2.0, "Waiting for PX4/MAVROS connection")
            rate.sleep()

    def enter_offboard(self):
        rospy.wait_for_service("/mavros/set_mode")
        rospy.wait_for_service("/mavros/cmd/arming")
        set_mode = rospy.ServiceProxy("/mavros/set_mode", SetMode)
        arm = rospy.ServiceProxy("/mavros/cmd/arming", CommandBool)

        rate = rospy.Rate(20)
        for _ in range(100):
            if rospy.is_shutdown():
                return
            self.publish_target()
            rate.sleep()

        deadline = rospy.Time.now() + rospy.Duration(10.0)
        while (
            not rospy.is_shutdown()
            and self.state.mode != "OFFBOARD"
            and rospy.Time.now() < deadline
        ):
            mode_result = set_mode(base_mode=0, custom_mode="OFFBOARD")
            if not mode_result.mode_sent:
                rospy.logwarn("PX4 did not accept the OFFBOARD request")
            self.publish_target()
            for _ in range(20):
                if (
                    rospy.is_shutdown()
                    or self.state.mode == "OFFBOARD"
                    or rospy.Time.now() >= deadline
                ):
                    break
                self.publish_target()
                rate.sleep()

        if self.state.mode != "OFFBOARD":
            rospy.logerr("PX4 did not enter OFFBOARD mode")
            return

        arm_result = arm(value=True)
        if not arm_result.success:
            rospy.logerr("PX4 arming failed")
            return

        rospy.loginfo("PX4 is armed in OFFBOARD mode")

    def run(self):
        self.wait_for_connection()
        if self.auto_arm and not rospy.is_shutdown():
            self.enter_offboard()
        elif not self.auto_arm:
            rospy.logwarn(
                "Publishing setpoints only; set auto_arm:=true to switch to OFFBOARD and arm"
            )

        rate = rospy.Rate(20)
        last_update = rospy.Time.now()
        while not rospy.is_shutdown():
            now = rospy.Time.now()
            self.integrate_velocity((now - last_update).to_sec())
            last_update = now
            self.publish_target()
            rate.sleep()


if __name__ == "__main__":
    rospy.init_node("px4_offboard_control")
    Px4OffboardControl().run()
