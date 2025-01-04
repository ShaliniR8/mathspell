from setuptools import setup, find_packages
import os

def install_spacy_model():
    os.system("python -m spacy download en_core_web_sm")

setup(
    name="mathspell",
    version="0.0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "spacy",
        "num2words",
    ],
    description="A library for converting numbers to words contextually.",
    long_description=open("README.md").read(),
    author="ShaliniR8",
    author_email="shaliniroy1008@gmail.com",
    url="https://github.com/ShaliniR8/mathspell",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)

# Automatically install the spaCy model after installing the package
install_spacy_model()
