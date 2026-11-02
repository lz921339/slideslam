#!/usr/bin/env python3
"""Bidirectional telemetry bridge between the simulated car and drone."""

import rospy
from nav_msgs.msg import Odometry
from std_msgs.msg import String


class CarDroneCommunication:
    def __init__(self):
        self.car_seen = False
        self.drone_seen = False

        self.car_to_drone = rospy.Publisher(
            "/communication/car_to_drone", Odometry, queue_size=10
        )
        self.drone_to_car = rospy.Publisher(
            "/communication/drone_to_car", Odometry, queue_size=10
        )
        self.status = rospy.Publisher(
            "/communication/status", String, queue_size=10, latch=True
        )

        car_odom_topic = rospy.get_param("~car_odom_topic", "/odom")
        drone_odom_topic = rospy.get_param("~drone_odom_topic", "/drone/odom")

        rospy.Subscriber(car_odom_topic, Odometry, self.forward_car_odometry)
        rospy.Subscriber(drone_odom_topic, Odometry, self.forward_drone_odometry)
        rospy.Timer(rospy.Duration(1.0), self.publish_status)

    def forward_car_odometry(self, message):
        self.car_seen = True
        self.car_to_drone.publish(message)

    def forward_drone_odometry(self, message):
        self.drone_seen = True
        self.drone_to_car.publish(message)

    def publish_status(self, _event):
        car = "online" if self.car_seen else "waiting"
        drone = "online" if self.drone_seen else "waiting"
        self.status.publish("car: {}; drone: {}; link: active".format(car, drone))


if __name__ == "__main__":
    rospy.init_node("car_drone_communication")
    CarDroneCommunication()
    rospy.spin()
