#!/usr/bin/env python3
"""Execute a 3D body-frame cmd_vel for the Gazebo drone model."""

import math

import rospy
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import GetModelState, SetModelState
from geometry_msgs.msg import Twist
from tf.transformations import euler_from_quaternion, quaternion_from_euler


class DroneCmdVelController:
    def __init__(self):
        self.model_name = rospy.get_param("~model_name", "drone")
        self.reference_frame = rospy.get_param("~reference_frame", "world")
        self.command_timeout = float(rospy.get_param("~command_timeout", 0.5))
        self.min_altitude = float(rospy.get_param("~min_altitude", 0.25))
        self.max_altitude = float(rospy.get_param("~max_altitude", 20.0))
        self.update_rate = float(rospy.get_param("~update_rate", 50.0))

        self.command = Twist()
        self.last_command_time = rospy.Time(0)
        self.last_update_time = None
        self.position = None
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0

        rospy.wait_for_service("/gazebo/get_model_state")
        rospy.wait_for_service("/gazebo/set_model_state")
        self.get_model_state = rospy.ServiceProxy(
            "/gazebo/get_model_state", GetModelState
        )
        self.set_model_state = rospy.ServiceProxy(
            "/gazebo/set_model_state", SetModelState
        )
        self._refresh_pose()

        cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "/robot1/cmd_vel")
        rospy.Subscriber(cmd_vel_topic, Twist, self._on_command, queue_size=10)
        rospy.Timer(rospy.Duration(1.0 / max(1.0, self.update_rate)), self._tick)
        rospy.loginfo("Drone cmd_vel controller ready on %s", cmd_vel_topic)

    def _on_command(self, message):
        self.command = message
        self.last_command_time = rospy.Time.now()

    def _refresh_pose(self):
        response = self.get_model_state(self.model_name, self.reference_frame)
        if not response.success:
            raise RuntimeError(
                "Gazebo model '{}': {}".format(
                    self.model_name, response.status_message
                )
            )
        self.position = [
            response.pose.position.x,
            response.pose.position.y,
            response.pose.position.z,
        ]
        self.roll, self.pitch, self.yaw = euler_from_quaternion(
            (
                response.pose.orientation.x,
                response.pose.orientation.y,
                response.pose.orientation.z,
                response.pose.orientation.w,
            )
        )

    def _tick(self, _event):
        now = rospy.Time.now()
        if now == rospy.Time(0) or self.position is None:
            return
        if self.last_update_time is None:
            self.last_update_time = now
            return

        dt = max(0.0, min(0.1, (now - self.last_update_time).to_sec()))
        self.last_update_time = now
        command = self.command
        if (now - self.last_command_time).to_sec() > self.command_timeout:
            command = Twist()

        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        world_x = cos_yaw * command.linear.x - sin_yaw * command.linear.y
        world_y = sin_yaw * command.linear.x + cos_yaw * command.linear.y
        self.position[0] += world_x * dt
        self.position[1] += world_y * dt
        self.position[2] = min(
            self.max_altitude,
            max(self.min_altitude, self.position[2] + command.linear.z * dt),
        )
        self.yaw += command.angular.z * dt

        state = ModelState()
        state.model_name = self.model_name
        state.reference_frame = self.reference_frame
        state.pose.position.x = self.position[0]
        state.pose.position.y = self.position[1]
        state.pose.position.z = self.position[2]
        (
            state.pose.orientation.x,
            state.pose.orientation.y,
            state.pose.orientation.z,
            state.pose.orientation.w,
        ) = quaternion_from_euler(self.roll, self.pitch, self.yaw)
        state.twist = command
        try:
            response = self.set_model_state(state)
            if not response.success:
                rospy.logwarn_throttle(
                    5.0, "Unable to move drone model: %s", response.status_message
                )
        except rospy.ServiceException as exc:
            rospy.logwarn_throttle(5.0, "Gazebo set_model_state failed: %s", exc)


if __name__ == "__main__":
    rospy.init_node("drone_cmd_vel_controller")
    DroneCmdVelController()
    rospy.spin()
