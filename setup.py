from setuptools import setup, find_packages

setup(
    name="alrmpet",
    version="1.0.0",
    description="Prefix any command to get notified when it finishes — with ASCII pets!",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "webhook": ["requests>=2.28.0"],
    },
    entry_points={
        "console_scripts": [
            "alrmpet=alrmpet.cli:main",
        ],
    },
)
