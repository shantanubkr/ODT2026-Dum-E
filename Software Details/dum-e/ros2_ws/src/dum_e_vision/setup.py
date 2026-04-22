from setuptools import find_packages, setup

package_name = "dum_e_vision"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="DUM-E",
    maintainer_email="todo@example.com",
    description="DUM-E vision node: sim Image or real MJPEG to /dume/target_coord",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "vision_node = dum_e_vision.vision_node:main",
        ],
    },
)
