import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="part_placement_tool",
    version="0.0.1",
    author="Ryan Wicks",
    author_email="ryancwicks@gmail.com",
    description="Tool for placing parts on a set of circuit boards.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ryancwicks/CNC-DrawingMachine",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    dependencies = [
        "pyserial"
        ]
)
