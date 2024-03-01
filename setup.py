from setuptools import setup, find_packages
import os


TANTO_VERSION='0.3.8'


with open("README.md", "r", encoding="utf-8") as readme_file:
    README = readme_file.read()

setup(
    name='tanto',
    version=TANTO_VERSION,
    url="https://github.com/mglambda/tanto",
    author="Marius Gerdes",
    author_email="integr@gmail.com",
    description="A video and audio editor with built-in screen reader and strong accessibility support.",
    long_description=README,
    long_description_content_type="text/markdown",
    license_files=["LICENSE"],
    scripts=["scripts/tanto"],
    packages=find_packages(include=['tanto']),
    install_requires=["dev-moviepy", "pyaudio", "pygame", "pygame-gui", "pygame-textinput", "sounddevice", "soundfile", "screeninfo"]
)

