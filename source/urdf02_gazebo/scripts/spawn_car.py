#!/usr/bin/env python3
"""Reliably spawn the unchanged car URDF after PX4 Gazebo is ready."""

import rospy
from gazebo_msgs.srv import GetModelState, SpawnModel
from geometry_msgs.msg import Pose
import os


def main():
    rospy.init_node("spawn_px4_companion_car")

    model_name = rospy.get_param("~model_name", "car")
    robot_description_param = rospy.get_param(
        "~robot_description_param", "/robot_description"
    )
    model_xml = rospy.get_param(robot_description_param)
    rospy.logwarn(
        "[RGBD DEBUG] model XML: car_rgbd_sensor=%s, safe_rgbd_plugin=%s",
        "car_rgbd_sensor" in model_xml,
        "libgazebo_ros_safe_rgbd.so" in model_xml,
    )
    plugin_path = "/home/yd/slideslam/demo05_ws/devel/lib/libgazebo_ros_safe_rgbd.so"
    rospy.logwarn(
        "[RGBD DEBUG] plugin file: exists=%s readable=%s size=%s path=%s",
        os.path.exists(plugin_path),
        os.access(plugin_path, os.R_OK),
        os.path.getsize(plugin_path) if os.path.exists(plugin_path) else "missing",
        plugin_path,
    )
    rospy.logwarn(
        "[RGBD DEBUG] GAZEBO_PLUGIN_PATH=%s",
        os.environ.get("GAZEBO_PLUGIN_PATH", "<unset>"),
    )
    rospy.logwarn(
        "[RGBD DEBUG] LD_LIBRARY_PATH=%s",
        os.environ.get("LD_LIBRARY_PATH", "<unset>"),
    )

    pose = Pose()
    pose.position.x = rospy.get_param("~x", 1.0)
    pose.position.y = rospy.get_param("~y", 0.0)
    pose.position.z = rospy.get_param("~z", 0.25)
    pose.orientation.w = 1.0

    rospy.loginfo("Waiting for Gazebo before spawning model '%s'", model_name)
    rospy.wait_for_service("/gazebo/get_model_state")
    rospy.wait_for_service("/gazebo/spawn_urdf_model")

    get_model_state = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)
    spawn_model = rospy.ServiceProxy("/gazebo/spawn_urdf_model", SpawnModel)

    if get_model_state(model_name, "world").success:
        rospy.logwarn("Gazebo model '%s' already exists", model_name)
        rospy.spin()
        return

    last_status = "unknown error"
    for attempt in range(1, 6):
        try:
            response = spawn_model(
                model_name=model_name,
                model_xml=model_xml,
                robot_namespace="/car",
                initial_pose=pose,
                reference_frame="world",
            )
        except rospy.ServiceException as exc:
            last_status = str(exc)
            rospy.logwarn("Car spawn attempt %d failed: %s", attempt, last_status)
            rospy.sleep(2.0)
            continue
        last_status = response.status_message
        if response.success:
            rospy.loginfo(
                "Spawned car at x=%.3f y=%.3f z=%.3f",
                pose.position.x,
                pose.position.y,
                pose.position.z,
            )
            rospy.logwarn(
                "[RGBD DEBUG] Gazebo accepted car XML; inspect gzserver for "
                "SafeRgbdPlugin Load marker"
            )
            rospy.spin()
            return
        rospy.logwarn("Car spawn attempt %d failed: %s", attempt, last_status)
        rospy.sleep(2.0)

    raise RuntimeError("Unable to spawn car: {}".format(last_status))


if __name__ == "__main__":
    main()
