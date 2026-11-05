from setuptools import setup, find_packages

setup(
    name="spectral-luthier",
    version="0.1.0",
    description="Autonomous Stem-Aware Spectral Mastering with Dynamic DSP",
    author="Agentic Systems 2026",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.12",
    install_requires=[
        "torch>=2.2.0",
        "torchaudio>=2.2.0",
        "demucs>=4.0.1",
        "pedalboard>=0.9.0",
        "librosa>=0.11.0",
        "soundfile>=0.13.0",
        "pyloudnorm>=0.1.1",
        "numpy>=2.0.0",
        "scipy>=1.13.0",
        "loguru>=0.7.2",
        "pydantic>=2.6.0",
        "typer>=0.9.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "spectral-luthier=spectral_luthier.cli:app",
        ],
    },
)
