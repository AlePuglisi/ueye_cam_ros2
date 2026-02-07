#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image

import numpy as np 
import os

import cv2

from cv_bridge import CvBridge

from datetime import datetime
import threading

class CameraSaverNode(Node):
    def __init__(self):
        super().__init__('mola_apriltag_estimation')
        
        # Subscriptions
        self.cameraR_sub = self.create_subscription(
            Image,
            '/ueye_right/ui_3260cp_right/image_raw',
            self.camera_imageL_callback,
            10
        )
        self.cameraL_sub = self.create_subscription(
            Image,
            '/ueye_left/ui_3260cp_left/image_raw',
            self.camera_imageR_callback,
            10
        )

        self._cv_bridge = CvBridge()
        self.left_image = None
        self.right_image = None
        self.lock = threading.Lock()

        # Create directory for saved images
        mode = 'calibration'
        if mode == 'calibration':
            self.save_dir = "/home/ale/camera/stereo/images/calibration/"
            # if not os.path.exists(self.save_dir):
            #     os.makedirs(self.save_dir)
            #     self.get_logger().info(f"Created directory: {self.save_dir}")\
        else: 
            self.save_dir = "/home/ale/camera/stereo/images/"

        self.image_num = 0 

        # Start display thread
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()

        self.get_logger().info('Ueye Camera Saver Node Initialized')



    def camera_imageL_callback(self, msg):
        try:
            cv_image = self._cv_bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            with self.lock:
                self.left_image = cv_image
        except Exception as e:
            self.get_logger().error(f"Left image conversion error: {e}")
    
    def camera_imageR_callback(self, msg):
        try:
            cv_image = self._cv_bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            with self.lock:
                self.right_image = cv_image
        except Exception as e:
            self.get_logger().error(f"Right image conversion error: {e}")

    def save_images(self):
        with self.lock:
            if self.left_image is not None and self.right_image is not None:
                # timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                # left_filename = os.path.join(self.save_dir, f'left_{timestamp}.png')
                # right_filename = os.path.join(self.save_dir, f'right_{timestamp}.png')
                left_filename = os.path.join(self.save_dir, f'left_{self.image_num}.png')
                right_filename = os.path.join(self.save_dir, f'right_{self.image_num}.png')     

                cv2.imwrite(left_filename, self.left_image)
                cv2.imwrite(right_filename, self.right_image)

                self.image_num += 1

                self.get_logger().info(f"Saved images:\n  {left_filename}\n  {right_filename}")
            else:
                self.get_logger().warn("Cannot save: one or both images not received yet")
    

    def display_loop(self):
        cv2.namedWindow('Left Camera', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Right Camera', cv2.WINDOW_NORMAL)
        
        while self.running and rclpy.ok():
            with self.lock:
                left_img = self.left_image.copy() if self.left_image is not None else None
                right_img = self.right_image.copy() if self.right_image is not None else None
            
            # Display images
            if left_img is not None:
                cv2.imshow('Left Camera', left_img)
            
            if right_img is not None:
                cv2.imshow('Right Camera', right_img)
            
            # Handle key press
            key = cv2.waitKey(33) & 0xFF  # ~30 Hz
            if key == ord('s'):
                self.save_images()
            elif key == ord('q'):
                self.get_logger().info("Quit requested")
                self.running = False
                break
        
        cv2.destroyAllWindows()

    def destroy_node(self):
        self.running = False
        if self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CameraSaverNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()