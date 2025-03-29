from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="schemic",
    version="1.0.0",
    author="Reed Graff",
    author_email="rangergraff@gmail.com",
    description="Simplify using Pydantic models with LLMs in a type-safe way",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/reedgraff/schemic",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
    ],
)
