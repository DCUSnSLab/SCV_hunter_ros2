import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_hunter_teleop = get_package_share_directory('hunter_teleop')
    pkg_hunter_base = get_package_share_directory('hunter_base')

    config_file_path = os.path.join(pkg_hunter_teleop, 'config', 'system_params.yaml')
    twist_mux_config = os.path.join(pkg_hunter_teleop, 'config', 'twist_mux.yaml')
    go2rtc_config = os.path.join(pkg_hunter_teleop, 'config', 'go2rtc.yaml')

    default_use_sim = 'false'
    default_use_remote = 'true'

    with open(config_file_path, 'r') as f:
        config = yaml.safe_load(f)
        launch_params = config.get('launch_params', {})
        default_use_sim = str(launch_params.get('use_sim', False)).lower()
        default_use_remote = str(launch_params.get('use_remote_teleop', True)).lower()
        print(f"[System] Loaded Config: use_sim={default_use_sim}, use_remote={default_use_remote}")

    use_remote_arg = DeclareLaunchArgument(
        'use_remote_teleop',
        default_value=default_use_remote,
    )
    
    use_sim_arg = DeclareLaunchArgument(
        'use_sim',
        default_value=default_use_sim,
    )


    # 1. Twist Mux (Condition: use_remote_teleop=true)
    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        output='screen',
        remappings={
            ('cmd_vel_out', 'cmd_vel')
        },
        parameters=[twist_mux_config],
        condition=IfCondition(LaunchConfiguration('use_remote_teleop'))
    )

    # 2. UDP Receiver (Condition: use_remote_teleop=true)
    udp_receiver_node = Node(
        package='hunter_teleop',
        executable='udp_teleop.py',
        output='screen',
        parameters=[config_file_path], # Load params from YAML
        condition=IfCondition(LaunchConfiguration('use_remote_teleop'))
    )

    # 2.1 Status Monitor (Condition: use_remote_teleop=true)
    status_monitor_node = Node(
        package='hunter_teleop',
        executable='teleop_status_node.py',
        output='screen',
        parameters=[{
            'remote_enabled': LaunchConfiguration('use_remote_teleop')
        }],
        condition=IfCondition(LaunchConfiguration('use_remote_teleop'))
    )

    # 3. go2rtc Media Server (Condition: use_remote_teleop=true)
    go2rtc_cmd = ExecuteProcess(
        cmd=['go2rtc', '-c', go2rtc_config],
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_remote_teleop'))
    )

    # 4. Hunter Base (Real Hardware) - Run only if use_sim is FALSE
    hunter_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_hunter_base, 'launch', 'hunter_base.launch.py')
        ),
        condition=UnlessCondition(LaunchConfiguration('use_sim'))
    )

    # 5. Mock Hunter Base (Simulation) - Run only if use_sim is TRUE
    mock_hunter_node = Node(
        package='hunter_teleop',
        executable='mock_hunter_base.py',
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_sim'))
    )

    return LaunchDescription([
        use_remote_arg,
        use_sim_arg,
        hunter_base_launch,
        mock_hunter_node,
        twist_mux_node,
        udp_receiver_node,
        status_monitor_node,
        # go2rtc_cmd
    ])
