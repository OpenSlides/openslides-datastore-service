import setuptools

# "datastore@git+https://github.com/OpenSlides/openslides-datastore-service",

with open("requirements/requirements-general.txt") as requirements_production:
    install_requires = [x.strip() for x in requirements_production.readlines()]

setuptools.setup(
    name="datastore",
    version="1.0.0",
    author="jsangmeister, FinnStutzenstein",
    author_email="joshua.sangmeister@openslides.com, finn.stutzenstein@openslides.com",
    description="Package for OS4 to provide direct access to the datastore",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    package_data={"datastore": ["py.typed", "shared/postgresql_backend/schema.sql"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
