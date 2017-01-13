from setuptools import setup

setup(
    name = "vbuild",
    version = "0.0.1",
    author = "Michael Nolan",
    author_email = "mtnolan2640@gmail.com",
    description = """A build script for compiling verilog files in project iCEStorm""",
    license = "MIT",
    keywords = "verilog vbuild icestorm",
    packages = ['vbuild'],
    entry_points = {
        'console_scripts': ['vbuild=vbuild.command_line:main'],
    }
)
