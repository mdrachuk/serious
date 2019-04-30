from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf8') as f:
    readme = f.read()

setup(
    name="serious",
    version="2019.4.dev6",
    packages=find_packages(exclude=("tests*",)),
    author="mdrachuk",
    author_email="misha@drach.uk",
    description="Easily serialize dataclasses to and from JSON",
    long_description=readme,
    long_description_content_type='text/markdown',
    url="https://github.com/mdrachuk/serious",
    license="Unlicense",
    keywords="dataclasses json marshalling",
    install_requires=[
        "dataclasses;python_version=='3.7'",
    ],
    python_requires=">=3.7",
    extras_require={
        "dev": ["pytest", "mypy", "hypothesis"]
    },
    include_package_data=True
)
