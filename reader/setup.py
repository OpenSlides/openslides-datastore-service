import setuptools


setuptools.setup(
    name="datastore_reader",
    version="1.0.0",
    author="jsangmeister",
    author_email="joshua.sangmeister@intevation.com",
    description="Helper package for the readerlib to provide access to reader methods",
    packages=setuptools.find_packages(exclude=["tests*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)