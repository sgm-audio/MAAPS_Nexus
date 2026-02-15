"""
CV Director - Semantic Multi-Camera Switching System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="cv-director",
    version="0.1.0",
    description="AI-powered semantic multi-camera switching for live streaming",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Agentic Systems 2026",
    python_requires=">=3.12",

    # Package discovery
    packages=find_packages(where="src"),
    package_dir={"": "src"},

    # Dependencies
    install_requires=[
        "opencv-python>=4.9.0",
        "mediapipe>=0.10.0",
        "webrtcvad>=2.0.10",
        "obs-websocket-py>=1.0.0",
        "typer>=0.9.0",
        "rich>=13.7.0",
        "pydantic>=2.6.0",
        "numpy>=1.24.0",
        "loguru>=0.7.0",
        "pyaudio>=0.2.14",  # For audio input
    ],

    # CLI entry point
    entry_points={
        "console_scripts": [
            "cv-director=cv_director.cli:app",
        ],
    },

    # Metadata
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video :: Capture",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="computer-vision camera-switching live-streaming obs mediapipe",
)
