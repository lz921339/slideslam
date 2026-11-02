#!/usr/bin/env python3
"""Publish Gazebo ground truth and the world-to-odom transform for the car."""

import rospy
import tf
from gazebo_msgs.srv import GetModelState
from nav_msgs.msg import Odometry
from tf.transformations import concatenate_matrices, inverse_matrix, translation_from_matrix, quaternion_from_matrix, quaternion_matrix


class GroundTruthOdom:
    def __init__(self):
        self.model_name = rospy.get_param("~model_name", "car")
        self.world_frame = rospy.get_param("~world_frame", "world")
        self.odom_frame = rospy.get_param("~odom_frame", "odom")
        self.base_frame = rospy.get_param("~base_frame", "base_footprint")

        self.publisher = rospy.Publisher(
            "/robot0/ground_truth/odom", Odometry, queue_size=10
        )
        self.broadcaster = tf.TransformBroadcaster()
        self.listener = tf.TransformListener()

        rospy.wait_for_service("/gazebo/get_model_state")
        self.get_model_state = rospy.ServiceProxy(
            "/gazebo/get_model_state", GetModelState
        )

    def publish(self, _event):
        try:
            state = self.get_model_state(self.model_name, self.world_frame)
        except rospy.ServiceException as exc:
            rospy.logwarn_throttle(5.0, "Gazebo ground truth query failed: %s", exc)
            return

        if not state.success:
            rospy.logwarn_throttle(
                5.0, "Gazebo has no model '%s': %s", self.model_name, state.status_message
            )
            return

        stamp = rospy.Time.now()
        pose = state.pose
        message = Odometry()
        message.header.stamp = stamp
        message.header.frame_id = self.world_frame
        message.child_frame_id = self.base_frame
        message.pose.pose = pose
        message.twist.twist = state.twist
        self.publisher.publish(message)

        try:
            odom_translation, odom_rotation = self.listener.lookupTransform(
                self.odom_frame, self.base_frame, rospy.Time(0)
            )
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            return

        world_to_base = concatenate_matrices(
            translation_matrix((pose.position.x, pose.position.y, pose.position.z)),
            quaternion_matrix((pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w)),
        )
        odom_to_base = concatenate_matrices(
            translation_matrix(odom_translation), quaternion_matrix(odom_rotation)
        )
        world_to_odom = concatenate_matrices(world_to_base, inverse_matrix(odom_to_base))
        world_translation = translation_from_matrix(world_to_odom)
        world_rotation = quaternion_from_matrix(world_to_odom)
        self.broadcaster.sendTransform(
            world_translation,
            world_rotation,
            stamp,
            self.odom_frame,
            self.world_frame,
        )


def translation_matrix(vector):
    matrix = quaternion_matrix((0.0, 0.0, 0.0, 1.0))
    matrix[0:3, 3] = vector
    return matrix


if __name__ == "__main__":
    rospy.init_node("ground_truth_odom")
    node = GroundTruthOdom()
    rospy.Timer(rospy.Duration(0.02), node.publish)
    rospy.spin()
