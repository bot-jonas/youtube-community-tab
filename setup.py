import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), "r") as f:
    long_description = f.read()

setup(
    name="youtube_community_tab",
    version="0.2.2.1",
    description="A python3 module to handle YouTube Community Tab",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/bot-jonas/youtube-community-tab",
    package_dir={"": "src"},
    install_requires=[
        "requests_cache",
    ],
    packages=find_packages(where="src"),
    zip_safe=False,
)
