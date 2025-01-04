import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import Float32MultiArray
from napari.qt.threading import thread_worker
from threading import Thread

import time

import napari
import numpy as np


viewer = napari.Viewer()

def update_phase_volume(vol: np.ndarray):
    layer_key = "Phase Volume"
    try:
        layer = viewer.layers[layer_key]
        layer.data = vol
    except KeyError:
        viewer.add_image(vol, name=layer_key)
    
class NapariStreamViewer(Node):
    def __init__(self):
        super().__init__("napari_stream_viewer")

        self.create_subscription(
            Float32MultiArray, 
            "phase_reconstruction", 
            self.volume_callback, 
            qos_profile_sensor_data)
        

    def volume_callback(self, msg: Float32MultiArray):
        
        self.get_logger().info(f"Got a new volume")
        volume = np.array(msg.data, dtype=np.float32)
        volume = volume.reshape((msg.layout.dim[0].size, msg.layout.dim[1].size, msg.layout.dim[2].size))
        yield volume

#@thread_worker(connect={'yielded': update_phase_volume})
def ros_runner(args=None):

    rclpy.init(args=args)
    try:
        napari_stream_viewer = NapariStreamViewer()
        rclpy.spin(napari_stream_viewer)

    finally:
        napari_stream_viewer.destroy_node()
        rclpy.shutdown()

def main(args=None):

    ros_thread = Thread(target=ros_runner).start()
    napari.run()
    ros_thread.join()
    
if __name__ == "__main__":
    main()
