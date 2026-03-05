#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import numpy as np

from geometry_msgs.msg import PoseStamped
from crazyflie_interfaces.srv import Takeoff, Land, GoTo

class WaypointControllerNode(Node):
    """
    A waypoint controller that makes the drone take off, hover,
    and fly through the circle track. 

    The goTo service is used for waypoint navigation. It handles position control, 
    altitude hold, and trajectory smoothing internally. 
    """
    def __init__(self):
        super().__init__('waypoint_controller_node')

        self.z_flight = 0.355
        self.speed = 0.5   

        self.waypoints = [
            # --- GATE 1 (at 1.0, 0.0, rotated 90 deg) ---
            np.array([1.0, -1.0, self.z_flight]),   # Approach Gate 1 
            np.array([1.0, 0.8, self.z_flight]),    # Fly through Gate 1

            # --- GATE 2 (at 2.5, 1.5, rotated 0 deg) ---
            np.array([1.8, 1.5, self.z_flight]),     
            np.array([3.2, 1.5, self.z_flight]),     

            # --- GATE 3 (at 4.0, 0.0, rotated 90 deg) ---
            np.array([4.0, 0.8, self.z_flight]),    
            np.array([4.0, -0.8, self.z_flight]),    

            # --- GATE 4 (at 2.5, -1.5, rotated 0 deg) ---
            np.array([3.2, -1.5, self.z_flight]),    
            np.array([1.8, -1.5, self.z_flight]),   

            np.array([1.0, -1.0, self.z_flight])    # Return and land 
        ]

        self.current_wp_idx = 0
        self.current_pos = np.zeros(3)
        self.is_flying = False
        self.goto_sent = False  # Track if we've issued a goTo for current waypoint
        self.state = 'INIT'     # INIT -> TAKEOFF -> NAVIGATE -> LAND -> DONE

        # Pose subscription
        self.pose_sub = self.create_subscription(
            PoseStamped, '/cf_1/pose', self.pose_callback, 10)

        # Services
        self.takeoff_client = self.create_client(Takeoff, '/cf_1/takeoff')
        self.land_client = self.create_client(Land, '/cf_1/land')
        self.goto_client = self.create_client(GoTo, '/cf_1/go_to')

        self.takeoff_client.wait_for_service()
        self.land_client.wait_for_service()
        self.goto_client.wait_for_service()

        # Control loop at 10 Hz
        self.timer = self.create_timer(0.1, self.control_loop)
        self.start_time = self.get_clock().now()

        # Start takeoff
        self.get_logger().info("Taking off...")
        self.send_takeoff(self.z_flight, 2.0)
        self.state = 'TAKEOFF'
        self.takeoff_time = self.get_clock().now()

    def send_takeoff(self, height, duration):
        req = Takeoff.Request()
        req.group_mask = 0
        req.height = float(height)
        req.duration = rclpy.duration.Duration(seconds=duration).to_msg()
        self.takeoff_client.call_async(req)

    def send_land(self, height, duration):
        req = Land.Request()
        req.group_mask = 0
        req.height = float(height)
        req.duration = rclpy.duration.Duration(seconds=duration).to_msg()
        self.land_client.call_async(req)

    def send_goto(self, x, y, z, yaw, duration):
        req = GoTo.Request()
        req.group_mask = 0
        req.relative = False
        req.goal.x = float(x)
        req.goal.y = float(y)
        req.goal.z = float(z)
        req.yaw = float(yaw)
        req.duration = rclpy.duration.Duration(seconds=duration).to_msg()
        self.goto_client.call_async(req)

    def pose_callback(self, msg: PoseStamped):
        self.current_pos[0] = msg.pose.position.x
        self.current_pos[1] = msg.pose.position.y
        self.current_pos[2] = msg.pose.position.z

    def control_loop(self):
        now = self.get_clock().now()

        if self.state == 'TAKEOFF':
            # Wait for takeoff to complete (2s duration + 1s buffer)
            dt = (now - self.takeoff_time).nanoseconds / 1e9
            if dt > 3.0:
                self.get_logger().info("Takeoff complete. Starting navigation.")
                self.state = 'NAVIGATE'
                # Skip waypoint 0 if we're already near it (it's the start position)
                if np.linalg.norm(self.current_pos[:2] - self.waypoints[0][:2]) < 0.4:
                    self.get_logger().info("Waypoint 0 reached! (start position)")
                    self.current_wp_idx = 1
                self.goto_sent = False

        elif self.state == 'NAVIGATE':
            if self.current_wp_idx >= len(self.waypoints):
                self.get_logger().info("All waypoints reached! Landing...")
                self.send_land(0.0, 3.0)
                self.state = 'LAND'
                return

            # Ignore [0,0,0] glitch
            if np.all(self.current_pos == 0):
                return

            target = self.waypoints[self.current_wp_idx]

            # If we haven't sent a goTo for this waypoint yet, send it
            if not self.goto_sent:
                dist = np.linalg.norm(target - self.current_pos)
                duration = max(dist / self.speed, 1.0)  # At least 1 second
                self.get_logger().info(
                    f"GoTo waypoint {self.current_wp_idx}: "
                    f"[{target[0]:.2f}, {target[1]:.2f}, {target[2]:.2f}] "
                    f"(dist={dist:.2f}m, dur={duration:.1f}s)")
                self.send_goto(target[0], target[1], target[2], 0.0, duration)
                self.goto_sent = True
                self.goto_time = now

            # Check if we've arrived (XY distance)
            dist_xy = np.linalg.norm(target[:2] - self.current_pos[:2])
            if dist_xy < 0.3:
                self.get_logger().info(f"Waypoint {self.current_wp_idx} reached!")
                self.current_wp_idx += 1
                self.goto_sent = False

        elif self.state == 'LAND':
            dt = (now - self.takeoff_time).nanoseconds / 1e9
            # Just wait for landing
            pass

        elif self.state == 'DONE':
            pass

def main(args=None):
    rclpy.init(args=args)
    node = WaypointControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
