cmake_minimum_required(VERSION 3.10)
project(scan2shape_launch)

set(CMAKE_CXX_STANDARD 17)

find_package(catkin REQUIRED)

catkin_package()

# The processing nodes live in the sibling script directory.  Register them
# with catkin so roslaunch/rosrun can resolve the executables from this package.
catkin_install_python(PROGRAMS
  ${CMAKE_CURRENT_SOURCE_DIR}/../script/infer_node.py
  ${CMAKE_CURRENT_SOURCE_DIR}/../script/process_cloud_node.py
  ${CMAKE_CURRENT_SOURCE_DIR}/../script/process_cloud_node_lidar_indoor.py
  ${CMAKE_CURRENT_SOURCE_DIR}/../script/process_cloud_node_outdoor.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
