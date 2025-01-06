import rclpy
from rclpy.qos import qos_profile_sensor_data
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from functools import partial
import logging

logging.basicConfig(filename="napari_stream_viewer.log", level=logging.INFO)

import time
from typing import Optional
from multiprocessing import Process, Queue, Pipe

import napari
import numpy as np

queue = Queue()
ros_p, napari_p = Pipe()
viewer: Optional[napari.Viewer] = None
update_times = []


class NapariStreamViewer(Node):
    def __init__(self):
        super().__init__("napari_stream_viewer")
        self.declare_parameter("streams", ["stream0", "stream1"])

        streams = self.get_parameter("streams").get_parameter_value().string_array_value

        for i, stream in enumerate(streams):
            self.create_subscription(
                Image,
                stream,
                partial(self.stream_callback, stream_id=i),
                qos_profile_sensor_data,
            )

        self.create_subscription(Float32MultiArray, "phase_reconstruction", self.volume_callback, 10)
        
        self.get_logger().info(f"Configured {len(streams)} streams")

        self._elapsed_times = []

    def stream_callback(self, msg: Image, stream_id: int):
        self.get_logger().info(f"Got a new frame on stream {stream_id}")
        im = np.ndarray(
            shape=(msg.height, msg.width),
            dtype=np.uint8,
            buffer=msg.data,
        )
        layer_key = f"Stream {stream_id}"
        ros_p.send((im, layer_key))

    def volume_callback(self, msg: Float32MultiArray):
        self.get_logger().info("Got a new volume")
        volume = np.array(msg.data, dtype=np.float32)
        volume = volume.reshape((msg.layout.dim[2].size, msg.layout.dim[1].size, msg.layout.dim[0].size))
        volume = volume.transpose((2, 0, 1))
        layer_key = "Phase Volume"
        ros_p.send((volume, layer_key))
        
    @property
    def elapsed_times(self):
        return self._elapsed_times


def add_image(args):
    global viewer
    (data, layer_key) = args
    try:
        tic = time.time()
        layer = viewer.layers[layer_key]
        layer._slice.image._view = data
        layer.events.set_data()
        toc = time.time() - tic
        logging.info(f"Update time: {toc*1e3} ms")  # in ms
    except KeyError:
        viewer.add_image([data], name=layer_key)


@napari.qt.thread_worker(connect={"yielded": add_image})
def process_pipe(p: Pipe):
    while True:
        v = p.recv()
        yield v


def run_viewer(pipe: Pipe):
    global viewer
    viewer = napari.Viewer()
    worker = process_pipe(pipe)
    napari.run()


def main(args=None):
    process = Process(target=run_viewer, args=(napari_p,), daemon=True)
    process.start()

    rclpy.init(args=args)

    napari_stream_viewer = NapariStreamViewer()

    rclpy.spin(napari_stream_viewer)

    process.terminate()

    napari_stream_viewer.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
