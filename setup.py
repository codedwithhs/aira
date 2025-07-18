from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the contents of your requirements file for the install_requires list
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

# Define all dependencies for development, including testing, linting, and formatting
dev_requirements = [
    "pytest>=8.4.1",  # The test runner
    "pytest-cov>=6.2.1",  # Generates test coverage reports
    "requests-mock>=1.12.1",  # For mocking HTTP requests in tests
    "black>=25.1.0",  # The code formatter
    "ruff>=0.12.2",  # The linter
    "pre-commit>=4.2.0",  # For running checks before commits
    "python-dotenv>=1.1.1",  # Loads environment variables from .env files for local development
    "pytest-dotenv>=0.5.2",  # Automatically loads environment variables from .env files during pytest runs
]

setup(
    # --- Core Metadata ---
    name="incident-aira",
    version="0.1.0",
    author="Himanshu Singhal",
    author_email="singhal425@gmail.com",
    description="The open-source AI agent that automates incident response.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codedwithhs/aira",
    license="Apache-2.0",
    # --- Package Configuration ---
    packages=find_packages(),
    # Tell setuptools to include non-Python files
    package_data={
        # Any file in the 'aira.templates' package will be included
        "aira.templates": ["*.yaml", "*.json"],
    },
    # Core runtime dependencies
    install_requires=requirements,
    # Extra dependencies for development. Install with: pip install -e ".[dev]"
    extras_require={
        "dev": dev_requirements,
    },
    # This creates the `aira` command-line script
    entry_points={
        "console_scripts": [
            "aira = aira.cli:app",
        ],
    },
    # --- Additional Metadata for PyPI ---
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
