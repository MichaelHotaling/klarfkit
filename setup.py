import os

import pkg_resources
from setuptools import setup, find_packages

setup(
    name="klarfkit",
    py_modules=["klarfkit"],
    version="0.0.2",
    description="Python utilities for loading, plotting, and editing wafer defect maps known as KLA Reference Files (KLARFs)",
    readme="README.md",
    python_requires=">=3.7",
    author="MichaelHotaling",
    url="https://github.com/MichaelHotaling/klarfkit",
    license="MIT",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        str(r)
        for r in pkg_resources.parse_requirements(
            open(os.path.join(os.path.dirname(__file__), "requirements.txt"))
        )
    ],
    include_package_data=False,
    extras_require={'dev': ['pytest']},
)
