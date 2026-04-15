from setuptools import find_packages, setup

package_name = "dum_e_controller"

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
    description="DUM-E state manager and joint_states publisher",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "dum_e_state_manager = dum_e_controller.dum_e_state_manager:main",
        ],
    },
)
