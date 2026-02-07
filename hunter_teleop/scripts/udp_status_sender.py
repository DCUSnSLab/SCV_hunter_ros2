#!/usr/bin/env python3
"""
UDP Status Sender Node
- HunterStatus, TeleopStatus 토픽 구독
- 서버로 UDP 패킷 전송 (20Hz)
"""
import rclpy
from rclpy.node import Node
from hunter_msgs.msg import HunterStatus
from hunter_teleop.msg import TeleopStatus
import socket
import struct
import time


class UdpStatusSenderNode(Node):
    # 패킷 포맷 (40 bytes)
    PACKET_FORMAT = '<2sHdffBBHfBbBBB3sH'
    HEADER = b'VS'

    def __init__(self):
        super().__init__('udp_status_sender_node')

        # Parameters
        self.declare_parameter('server_ip', '127.0.0.1')
        self.declare_parameter('server_port', 5001)
        self.declare_parameter('send_rate', 20.0)

        self.server_ip = self.get_parameter('server_ip').value
        self.server_port = self.get_parameter('server_port').value
        self.send_rate = self.get_parameter('send_rate').value

        # UDP Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Subscriptions
        self.create_subscription(
            HunterStatus, 'hunter_status', self.cb_hunter_status, 10
        )
        self.create_subscription(
            TeleopStatus, 'teleop_status', self.cb_teleop_status, 10
        )

        # Cached Data
        self.hunter_data = None
        self.teleop_data = None
        self.seq_number = 0

        # Timer
        period = 1.0 / self.send_rate
        self.timer = self.create_timer(period, self.send_status)

        self.get_logger().info(
            f'UDP Status Sender started -> {self.server_ip}:{self.server_port} @ {self.send_rate}Hz'
        )

    def cb_hunter_status(self, msg: HunterStatus):
        self.hunter_data = msg

    def cb_teleop_status(self, msg: TeleopStatus):
        self.teleop_data = msg

    def send_status(self):
        packet = self._build_packet()
        try:
            self.sock.sendto(packet, (self.server_ip, self.server_port))
        except Exception as e:
            self.get_logger().warn(f'Send failed: {e}')
        self.seq_number = (self.seq_number + 1) & 0xFFFF

    def _build_packet(self) -> bytes:
        """40 byte 패킷 생성"""
        # HunterStatus 기본값
        linear_vel = 0.0
        steering_angle = 0.0
        vehicle_state = 0
        control_mode = 0
        error_code = 0
        battery_volt = 0.0

        # TeleopStatus 기본값
        remote_enabled = 0
        current_mode = -1
        nav_active = 0
        teleop_active = 0
        final_active = 0

        if self.hunter_data:
            linear_vel = self.hunter_data.linear_velocity
            steering_angle = self.hunter_data.steering_angle
            vehicle_state = self.hunter_data.vehicle_state
            control_mode = self.hunter_data.control_mode
            error_code = self.hunter_data.error_code
            battery_volt = self.hunter_data.battery_voltage

        if self.teleop_data:
            remote_enabled = self.teleop_data.remote_enabled
            current_mode = self.teleop_data.current_mode
            nav_active = int(self.teleop_data.nav_active)
            teleop_active = int(self.teleop_data.teleop_active)
            final_active = int(self.teleop_data.final_active)

        # 체크섬
        checksum = int(abs(linear_vel * 100 + steering_angle * 100 + battery_volt)) & 0xFFFF

        return struct.pack(
            self.PACKET_FORMAT,
            self.HEADER,
            self.seq_number,
            time.time(),
            linear_vel,
            steering_angle,
            vehicle_state,
            control_mode,
            error_code,
            battery_volt,
            remote_enabled,
            current_mode,
            nav_active,
            teleop_active,
            final_active,
            b'\x00\x00\x00',  # Reserved
            checksum
        )


def main(args=None):
    rclpy.init(args=args)
    node = UdpStatusSenderNode()
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
