import setuptools
from slurmui._version import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="slurmui",
    version=__version__,
    author="Norman Müller",
    author_email="normanm@meta.com",
    url="https://github.com/SirWyver/slurmui",
    description="Terminal UI for Slurm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": ["slurmui=slurmui.slurmui_cli:slurmui_cli"],
    },
    install_requires=[
        "textual",
        "pandas"
    ],
)
