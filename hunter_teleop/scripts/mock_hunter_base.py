#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import time
import math

class MockHunterBase(Node):
    def __init__(self):
        super().__init__('mock_hunter_base')
        
        # Subscribe to final cmd_vel (Output of TwistMux)
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # Publish Fake Odometry
        self.odom_publisher = self.create_publisher(Odometry, 'odom', 10)
        
        # State
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.linear_vel = 0.0
        self.angular_vel = 0.0
        self.last_time = time.time()
        
        # Timer (50Hz)
        self.timer = self.create_timer(0.02, self.update_odom)
        
        self.get_logger().info("Mock Hunter Base Started. Listening to /cmd_vel...")

    def cmd_vel_callback(self, msg):
        # Update target velocity
        self.linear_vel = msg.linear.x
        self.angular_vel = msg.angular.z
        # self.get_logger().info(f"Received Command: Lin={self.linear_vel:.2f}, Ang={self.angular_vel:.2f}")

    def update_odom(self):
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Simple Kinematics (Bicycle Model approximation)
        self.x += self.linear_vel * math.cos(self.theta) * dt
        self.y += self.linear_vel * math.sin(self.theta) * dt
        self.theta += self.angular_vel * dt
        
        # Publish Odom Msg
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        
        # Position
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        
        # Orientation (Yaw to Quaternion)
        # Simplified for 2D
        odom.pose.pose.orientation.z = math.sin(self.theta / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.theta / 2.0)
        
        # Velocity
        odom.twist.twist.linear.x = self.linear_vel
        odom.twist.twist.angular.z = self.angular_vel
        
        self.odom_publisher.publish(odom)

def main(args=None):
    rclpy.init(args=args)
    node = MockHunterBase()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
