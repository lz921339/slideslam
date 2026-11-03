#!/usr/bin/env python3
"""Normalize Gazebo's world-frame odometry and publish odom -> base TF."""

import copy
import time

import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry


class OdomTfFallback(object):
    def __init__(self):
        self.odom_topic = rospy.get_param("~odom_topic", "/robot1/odom_raw")
        self.odom_output_topic = rospy.get_param(
            "~odom_output_topic", "/robot1/odom"
        )
        self.odom_frame = rospy.get_param("~odom_frame", "robot1/odom")
        self.base_frame = rospy.get_param("~base_frame", "robot1/base_link")
        self.mode = rospy.get_param("~mode", "auto")       # auto | always
        self.probe_timeout = float(rospy.get_param("~probe_timeout", 3.0))

        self.buffer = tf2_ros.Buffer()
        self.listener = tf2_ros.TransformListener(self.buffer)
        self.broadcaster = tf2_ros.TransformBroadcaster()

        self.decided = self.mode == "always"
        self.publishing = self.decided
        self.probe_deadline = time.time() + self.probe_timeout
        self.latest = None
        self.last_tf_stamp = None
        self.frame_warned = False
        self.publisher = rospy.Publisher(
            self.odom_output_topic, Odometry, queue_size=20
        )

        rospy.Subscriber(self.odom_topic, Odometry, self.on_odom, queue_size=20)
        rospy.Timer(rospy.Duration(0.05), self.tick)

    def on_odom(self, msg):
        normalized = copy.deepcopy(msg)
        normalized.header.frame_id = self.odom_frame
        normalized.child_frame_id = self.base_frame
        self.latest = normalized
        self.publisher.publish(normalized)

    def tick(self, _event):
        if not self.decided and not self._decide():
            return
        if not self.publishing or self.latest is None:
            return

        msg = self.latest
        if self.last_tf_stamp == msg.header.stamp:
            return
        self.last_tf_stamp = msg.header.stamp
        if msg.header.frame_id and msg.header.frame_id != self.odom_frame and not self.frame_warned:
            rospy.logwarn("%s: odom header.frame_id='%s' != '%s', TF may be inconsistent",
                          rospy.get_name(), msg.header.frame_id, self.odom_frame)
            self.frame_warned = True

        transform = TransformStamped()
        transform.header.stamp = msg.header.stamp
        transform.header.frame_id = self.odom_frame
        transform.child_frame_id = self.base_frame
        transform.transform.translation.x = msg.pose.pose.position.x
        transform.transform.translation.y = msg.pose.pose.position.y
        transform.transform.translation.z = msg.pose.pose.position.z
        transform.transform.rotation = msg.pose.pose.orientation
        self.broadcaster.sendTransform(transform)

    def _decide(self):
        """返回 True 表示已做出决定（无论最终发不发）。"""
        try:
            exists = self.buffer.can_transform(
                self.odom_frame, self.base_frame, rospy.Time(0), rospy.Duration(0.0))
        except Exception:                                  # noqa: BLE001 - tf 会抛多种异常
            exists = False
        if exists:
            rospy.loginfo("%s: %s -> %s already broadcast by another node, staying idle",
                          rospy.get_name(), self.odom_frame, self.base_frame)
            self.decided = True
            self.publishing = False
            return True
        if time.time() < self.probe_deadline:
            return False
        rospy.logwarn("%s: nobody publishes %s -> %s, taking over from %s",
                      rospy.get_name(), self.odom_frame, self.base_frame, self.odom_topic)
        self.decided = True
        self.publishing = True
        return True


if __name__ == "__main__":
    rospy.init_node("drone_odom_tf")
    OdomTfFallback()
    rospy.spin()
