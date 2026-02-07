#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from hunter_teleop.msg import TeleopStatus
from hunter_msgs.msg import HunterStatus
import time

class TeleopStatusNode(Node):
    def __init__(self):
        super().__init__('teleop_status_node')
        
        self.declare_parameter('timeout', 0.5) 
        self.timeout = self.get_parameter('timeout').value
        
        self.declare_parameter('remote_enabled', True)
        self.remote_enabled_param = self.get_parameter('remote_enabled').value

        self.create_subscription(Twist, 'cmd_vel_nav', self.cb_nav, 10)
        self.create_subscription(Twist, 'cmd_vel_teleop', self.cb_teleop, 10)
        self.create_subscription(Twist, 'cmd_vel', self.cb_final, 10)
        self.create_subscription(HunterStatus, 'hunter_status', self.cb_hunter, 10)

        self.status_pub = self.create_publisher(TeleopStatus, 'teleop_status', 10)

        self.last_nav_time = 0.0
        self.last_teleop_time = 0.0
        self.last_final_time = 0.0
        
        self.hunter_control_mode = 0 
        
        self.timer = self.create_timer(0.03, self.update_status)

    def cb_nav(self, msg): self.last_nav_time = time.time()
    def cb_teleop(self, msg): self.last_teleop_time = time.time()
    def cb_final(self, msg): self.last_final_time = time.time()
    
    def cb_hunter(self, msg):
        self.hunter_control_mode = msg.control_mode 

    def update_status(self):
        now = time.time()
        
        # 1. Check Topic Activity
        active_nav = (now - self.last_nav_time) < self.timeout
        active_teleop = (now - self.last_teleop_time) < self.timeout
        active_final = (now - self.last_final_time) < self.timeout

        # 2. Determine Current Mode
        current_mode = -1 # Idle
        
        if active_teleop:
            current_mode = 2 # UDP Remote
        elif active_nav:
            current_mode = 1 # Auto
        
        # Override if HW RC is active (Assuming 1 is RC mode)
        if self.hunter_control_mode == 1: 
             current_mode = 0 # Hardware Controller

        # 3. Publish Custom Message
        msg = TeleopStatus()
        msg.remote_enabled = 1 if self.remote_enabled_param else 0
        msg.current_mode = int(current_mode)
        msg.nav_active = active_nav
        msg.teleop_active = active_teleop
        msg.final_active = active_final

        self.status_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = TeleopStatusNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()