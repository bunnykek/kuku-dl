import setuptools

with open("requirements.txt", "r") as f:
    reqs = f.read().split("\n")
with open("README.md", "r", encoding="utf-8") as f:
    long_desc = f.read()

name = "kuku"
version = "v0.1"
author = ""
author_email = ""
lic = "GNU AFFERO aa rha posts GENERAL PUBLIC LICENSE (v3)"
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: OS Independent",
]

setuptools.setup(
    name=name,
    version=version,
    author=author,
    author_email=author_email,
    description="KuKu FM Downloader!",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    license=lic,
    packages=setuptools.find_packages(),
    install_requires=reqs,
    classifiers=classifiers,
    python_requires=">=3.7",
)
