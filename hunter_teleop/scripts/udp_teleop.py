#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import socket
import struct
import time

class UdpReceiverNode(Node):
    def __init__(self):
        super().__init__('udp_teleop_node')
        
        self.declare_parameter('port', 5000)
        self.declare_parameter('timeout', 0.5)
        self.declare_parameter('max_linear_vel', 1.5)  # Hunter SE Spec
        self.declare_parameter('max_angular_vel', 2.0) # Rad/s
        
        self.port = self.get_parameter('port').value
        self.timeout = self.get_parameter('timeout').value
        self.max_linear_vel = self.get_parameter('max_linear_vel').value
        self.max_angular_vel = self.get_parameter('max_angular_vel').value

        self.publisher_ = self.create_publisher(Twist, 'cmd_vel_teleop', 10)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.setblocking(False)
        
        self.get_logger().info(f'UDP Receiver listening on 0.0.0.0:{self.port}')

        self.last_packet_time = 0.0
        self.is_active = False
        self.stop_pub_end_time = 0.0
        self.waiting_logged = False

        self.get_logger().info('Waiting for server connection...')

        self.timer = self.create_timer(0.02, self.timer_callback)

    def timer_callback(self):
        try:
            # Drain buffer
            data = None
            while True:
                try:
                    packet, addr = self.sock.recvfrom(1024)
                    data = packet
                except BlockingIOError:
                    break
            
            if data:
                self.process_packet(data)
                
        except Exception as e:
            self.get_logger().error(f'Socket error: {e}')
        
        current_time = time.time()
        time_since_last = current_time - self.last_packet_time if self.last_packet_time > 0 else float('inf')

        if time_since_last > self.timeout:
            if self.is_active:
                self.get_logger().warn('Connection lost! Releasing control to Auto.')
                self.is_active = False
                self.waiting_logged = False
                self.stop_pub_end_time = current_time + 0.5

            if not self.waiting_logged:
                self.get_logger().info('Waiting for server connection...')
                self.waiting_logged = True

            if current_time < self.stop_pub_end_time:
                self.publish_stop()

    def process_packet(self, data):
        if len(data) != 12: return

        try:
            header, linear, angular, checksum = struct.unpack('<2sffH', data)
            if header != b'HT': return

            if not self.is_active:
                self.get_logger().info('Server connected! Teleop active.')

            self.last_packet_time = time.time()
            self.is_active = True
            self.waiting_logged = False
            self.stop_pub_end_time = 0.0

            msg = Twist()
            msg.linear.x = max(min(linear, self.max_linear_vel), -self.max_linear_vel)
            msg.angular.z = max(min(angular, self.max_angular_vel), -self.max_angular_vel)
            self.publisher_.publish(msg)
        except struct.error:
            pass

    def publish_stop(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = UdpReceiverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.sock.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()