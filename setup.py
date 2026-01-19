from pathlib import Path

from setuptools import find_packages, setup

BASE_DIR = Path(__file__).parent
README_PATH = BASE_DIR / "README.md"
REQUIREMENTS_PATH = BASE_DIR / "requirements.txt"

long_description = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
install_requires = []
if REQUIREMENTS_PATH.exists():
    install_requires = [
        line.strip()
        for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="ticktick-automations",
    version="0.1.0",
    description="Automations and utilities for the TickTick task manager.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Arjun Agarwal",
    url="https://github.com/arjunagarwal899/ticktick_automations",
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=install_requires,
    license="GPL-3.0-only",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Source": "https://github.com/arjunagarwal899/ticktick_automations",
        "Issues": "https://github.com/arjunagarwal899/ticktick_automations/issues",
    },
)
