from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the contents of your requirements file
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    # --- Core Metadata ---
    name="incident-compass",
    version="0.1.0",
    author="Himanshu Singhal",
    author_email="singhal425@gmail.com",
    description="The open-source AI agent that automates incident response.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codedwithhs/compass",
    license="Apache-2.0",

    # --- Package Configuration ---
    # find_packages() automatically finds all packages (directories with __init__.py)
    packages=find_packages(),

    # The list of dependencies required for the project to run
    install_requires=requirements,

    # This creates the `compass` command-line script
    entry_points={
        'console_scripts': [
            'compass = compass.cli:app',
        ],
    },

    # --- Additional Metadata for PyPI ---
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)