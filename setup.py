"""
Setup script for the allyanonimiser package.
"""

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py


class StructureTestCommand(build_py):
    """A custom command to run the package structure tests."""
    
    description = 'Run package structure tests'
    
    def run(self):
        """Run the package structure tests."""
        print("Running package structure tests...")
        result = os.system("python tests/run_package_tests.py")
        if result != 0:
            sys.exit(result)
        return super().run()

setup(
    name="allyanonimiser",
    version="0.1.7",
    description="Australian-focused PII detection and anonymization for the insurance industry",
    author="Stephen Oates",
    author_email="stephen.j.a.oates@gmail.com",
    url="https://github.com/srepho/Allyanonimiser",
    packages=find_packages(),
    install_requires=[
        "spacy>=3.5.0",
        "presidio-analyzer>=2.2.0",
        "presidio-anonymizer>=2.2.0"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    cmdclass={
        "structure_test": StructureTestCommand,
    },
)