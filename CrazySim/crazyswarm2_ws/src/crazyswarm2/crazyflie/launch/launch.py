import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from launch.conditions import LaunchConfigurationEquals
from launch.substitutions import LaunchConfiguration

def parse_yaml(context):
    # Load the crazyflies YAML file
    crazyflies_yaml = LaunchConfiguration('crazyflies_yaml_file').perform(context)
    with open(crazyflies_yaml, 'r') as file:
        crazyflies = yaml.safe_load(file)

    # Server params
    server_yaml = os.path.join(
        get_package_share_directory('crazyflie'),
        'config',
        'server.yaml')

    with open(server_yaml, 'r') as ymlfile:
        server_yaml_content = yaml.safe_load(ymlfile)

    server_params = [crazyflies] + [server_yaml_content['/crazyflie_server']['ros__parameters']]
    
    # Robot description
    urdf = os.path.join(
        get_package_share_directory('crazyflie'),
        'urdf',
        'crazyflie_description.urdf')

    with open(urdf, 'r') as f:
        robot_desc = f.read()

    server_params[1]['robot_description'] = robot_desc

    return [
        # Only the Python backend is kept to support the CFlib-only workflow
        Node(
            package='crazyflie',
            executable='crazyflie_server.py',
            condition=LaunchConfigurationEquals('backend','cflib'),
            name='crazyflie_server',
            output='screen',
            parameters= server_params,
        )
    ]

def generate_launch_description():
    pkg_share = get_package_share_directory('crazyflie')

    default_crazyflies_yaml_path = os.path.join(pkg_share, 'config', 'crazyflies.yaml')
    default_rviz_config_path = os.path.join(pkg_share, 'config', 'config.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('crazyflies_yaml_file', default_value=default_crazyflies_yaml_path),
        DeclareLaunchArgument('rviz_config_file', default_value=default_rviz_config_path),
        # Default backend is changed to 'cflib' per your bloat analysis requirements
        DeclareLaunchArgument('backend', default_value='cflib'),
        DeclareLaunchArgument('rviz', default_value='False'),
        DeclareLaunchArgument('gui', default_value='True'),
        
        OpaqueFunction(function=parse_yaml),

        Node(
            condition=LaunchConfigurationEquals('rviz', 'True'),
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', LaunchConfiguration('rviz_config_file')],
        ),
        Node(
            condition=LaunchConfigurationEquals('gui', 'True'),
            package='crazyflie',
            executable='gui.py',
            name='gui',
        ),
    ])
