import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_desc = fh.read()

setuptools.setup(
    name = "gofilepy-api",
    version = "0.2.9",
    author = "m0bb1n",
    author_email = "99den0@gmail.com",
    description = "A python wrapper for Gofile REST API",
    long_description = long_desc,
    long_description_content_type = "text/markdown",
    license="MIT",
    url = "https://github.com/m0bb1n/gofilepy",
    packages = setuptools.find_packages(),
    install_requires = [
        'requests'
    ],
    classifiers = [
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ]
)
