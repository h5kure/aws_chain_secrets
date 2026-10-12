import setuptools

with open("README.rst", "r", encoding='utf-8') as readme:
    long_description = readme.read()

setuptools.setup(
    name="aws_chain_secrets",
    version='1.0.3',
    author="Hyouk Oh",
    author_email="h.5.kure@gmail.com",
    description="This aims to enable the use of one or more secrets from AWS SecretsManager.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/h5kure/aws_chain_secrets",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    package_data={"": ["py.typed"]},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=['boto3']
)
