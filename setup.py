"""
Setup script for the Allyanonimiser package.
"""

from setuptools import setup, find_packages

# Read the content of README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="allyanonimiser",
    version="0.1.0",
    author="Stephen Oates",
    author_email="stephen.j.a.oates@gmail.com",
    description="Australian-focused PII detection and anonymization for the insurance industry",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/srepho/Allyanonimiser",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "spacy>=3.5.0",
        "presidio-analyzer>=2.2.0",
        "presidio-anonymizer>=2.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=5.0.0",
            "mypy>=0.9.0",
        ],
        "llm": [
            "openai>=0.27.0",
            "anthropic>=0.3.0",
        ],
    },
)