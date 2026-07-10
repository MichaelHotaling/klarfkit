import os

from setuptools import setup, find_packages


def _read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    with open(req_path) as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


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
    install_requires=_read_requirements(),
    include_package_data=False,
    extras_require={'dev': ['pytest']},
)
