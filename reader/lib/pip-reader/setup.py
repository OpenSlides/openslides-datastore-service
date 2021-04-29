import setuptools


# hard code the dependencies since we unfortunately do not have access to the requirements file
install_requires = ["flask", "psycopg2", "fastjsonschema", "gunicorn", "dacite"]
for dep in ["reader", "shared"]:
    # See https://stackoverflow.com/a/64921671 for different pip/setuptools formats
    # Installing this package will only work through pip
    install_requires.append(f"datastore_{dep}@git+https://github.com/jsangmeister/openslides-datastore-service@pip-package#subdirectory={dep}")

setuptools.setup(
    name="readerlib",
    version="1.0.0",
    author="jsangmeister",
    author_email="joshua.sangmeister@intevation.com",
    description="Package for OS4 to provide direct read access to the datastore",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
