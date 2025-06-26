from setuptools import setup, find_packages

setup(
    name="adaptive-checkpointer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "cbor2>=5.4.6",
        "zstandard>=0.19.0",
        "numpy>=1.24.3",
        "psutil>=5.9.5"
    ],
    extras_require={
        "omnetpp": ["omnetpp"],
        "redis": ["redis>=4.5.5"],
        "s3": ["boto3>=1.26.142"]
    },
    entry_points={
        "console_scripts": [
            "ckpt-benchmark=adaptive_checkpointer.benchmark:main"
        ]
    }
)
