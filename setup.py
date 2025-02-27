"""
Setup script for the allyanonimiser package.
"""

from setuptools import setup, find_packages

setup(
    name="allyanonimiser",
    version="0.1.2",
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
)