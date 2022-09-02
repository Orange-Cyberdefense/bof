import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="boiboite-opener-framework",
    version="1.2.0",
    author="Claire Vacherot",
    author_email="claire.vacherot@orange.com",
    description="Industrial network protocols testing framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Orange-Cyberdefense/bof",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=['scapy==2.5.0rc1', 'packaging'],
    python_requires='>=3.6',
)
