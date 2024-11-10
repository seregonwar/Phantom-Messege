from setuptools import setup, find_packages
import os

def read_requirements(filename):
    with open(filename, encoding='utf-8') as f:  # Specify UTF-8 encoding to avoid UnicodeDecodeError
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="Phantom Messenger",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'ngl-sender=src.main:main',
            'ngl-sender-gui=src.main:main',  # Alias for the GUI version
        ],
    },
    package_data={
        'src': [
            'text_generator/libraries/*/*.json',
            'gui/styles/*.qss',
        ],
    },
    author="Seregonwar",
    author_email="seregonwar@gmail.com",
    description="An advanced tool for sending messages on NGL.link or any other platform with a graphical interface",
    long_description=open("README.md", encoding='utf-8').read() if os.path.exists("README.md") else "",  # Specify UTF-8 encoding
    long_description_content_type="text/markdown",
    keywords="ngl messaging automation gui pyqt6",
    url="https://github.com/Seregonwar/Phantom-Messenger",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.7",
)