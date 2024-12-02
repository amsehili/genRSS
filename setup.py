from setuptools import setup, find_packages
import ast
import re

_version_re = re.compile(r"__version__\s+=\s+(.*)")

# Extract version from __init__.py
with open("src/generss/__init__.py", "rt") as f:
    version = str(ast.literal_eval(_version_re.search(f.read()).group(1)))

# Read long description from README.md
with open("README.md", "rt") as f:
    long_description = f.read()

setup(
    name="generss",
    version=version,
    description="Generate RSS feeds from media files in a directory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Amine Sehili",
    author_email="amine.sehili@example.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Communications :: File Sharing",
        "Topic :: Utilities",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.4",
    install_requires=[
        "mutagen",
        "eyed3",
    ],
    entry_points={
        "console_scripts": [
            "genRSS=generss:main",
        ],
    },
)
