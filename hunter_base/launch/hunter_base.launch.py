import os
import launch
import launch_ros

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='false',
                                             description='Use simulation clock if true')

    port_name_arg = DeclareLaunchArgument('port_name', default_value='can0',
                                         description='CAN bus name, e.g. can0')
    odom_frame_arg = DeclareLaunchArgument('odom_frame', default_value='odom',
                                           description='Odometry frame id')
    base_link_frame_arg = DeclareLaunchArgument('base_frame', default_value='base_link',
                                                description='Base link frame id')
    odom_topic_arg = DeclareLaunchArgument('odom_topic_name', default_value='odometry/wheel',
                                           description='Odometry topic name')
    publish_tf_arg = DeclareLaunchArgument('publish_tf', default_value='false',
                                           description='Whether to publish TF (odom->base_link)')

    simulated_robot_arg = DeclareLaunchArgument('simulated_robot', default_value='false',
                                                   description='Whether running with simulator')
    sim_control_rate_arg = DeclareLaunchArgument('control_rate', default_value='50',
                                                 description='Simulation control loop update rate')
    
    # hunter_base SIGABRTs (ugv_sdk std::terminate) if can0 is down —
    # exactly what killed the 2026-07-14 field run 0.2 s after launch.
    # Bring the interface up if needed (sudoers.d/scv-can0 allows this
    # exact command without a password), then start the driver delayed.
    can0_up = ExecuteProcess(
        cmd=['bash', '-c',
             'ip link show can0 2>/dev/null | grep -q "state UP" || '
             'sudo -n /usr/sbin/ip link set can0 up type can bitrate 500000 || '
             'echo "[hunter_base.launch] ERROR: can0 DOWN and bring-up failed — hunter_base will not survive"'],
        output='screen')

    hunter_base_node = launch_ros.actions.Node(
        package='hunter_base',
        executable='hunter_base_node',
        output='screen',
        emulate_tty=True,
        respawn=True,
        respawn_delay=2.0,
        parameters=[{
                'use_sim_time': launch.substitutions.LaunchConfiguration('use_sim_time'),
                'port_name': launch.substitutions.LaunchConfiguration('port_name'),
                'odom_frame': launch.substitutions.LaunchConfiguration('odom_frame'),
                'base_frame': launch.substitutions.LaunchConfiguration('base_frame'),
                'odom_topic_name': launch.substitutions.LaunchConfiguration('odom_topic_name'),
                'publish_tf': launch.substitutions.LaunchConfiguration('publish_tf'),
                'simulated_robot': launch.substitutions.LaunchConfiguration('simulated_robot'),
                'control_rate': launch.substitutions.LaunchConfiguration('control_rate'),
        }])

    velocity_extractor_node = launch_ros.actions.Node(
        package='hunter_base',
        executable='velocity_extractor_node',
        output='screen',
        emulate_tty=True)

    hunter_state_parser_node = launch_ros.actions.Node(
        package='hunter_base',
        executable='hunter_state_parser_node',
        output='screen',
        emulate_tty=True)

    return LaunchDescription([
        use_sim_time_arg,
        port_name_arg,
        odom_frame_arg,
        base_link_frame_arg,
        odom_topic_arg,
        publish_tf_arg,
        simulated_robot_arg,
        sim_control_rate_arg,
        can0_up,
        launch.actions.TimerAction(period=2.0, actions=[hunter_base_node]),
        velocity_extractor_node,
        hunter_state_parser_node
    ])
