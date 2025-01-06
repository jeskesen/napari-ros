import os
from glob import glob
from setuptools import setup

package_name = "napari_ros"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
    ],
    install_requires=["setuptools", "wheel", "napari"],
    zip_safe=True,
    maintainer="Alan Liddell",
    maintainer_email="alan.c.liddell@gmail.com",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "viewer = napari_ros.viewer:main",
            "stream_viewer = napari_ros.stream_viewer:main",
        ],
        "napari.manifest": ["napari-ros = napari_ros:napari.yaml"],
    },
)
