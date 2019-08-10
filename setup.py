from setuptools import setup, find_packages

import version


def readme():
    with open('README.md', 'r', encoding='utf8') as f:
        return f.read()


setup(
    name='serious',
    version=version.__version__,
    packages=find_packages(exclude=("tests*",)),
    author='mdrachuk',
    author_email='misha@drach.uk',
    description="Easily serialize dataclasses to and from JSON",
    long_description=readme(),
    long_description_content_type='text/markdown',
    url="https://github.com/mdrachuk/serious",
    license="Unlicense",
    keywords="dataclasses json serialization",
    python_requires=">=3.7",
    project_urls={
        'Pipelines': 'https://dev.azure.com/misha-drachuk/serious',
        'Source': 'https://github.com/mdrachuk/serious/',
    },
    extras_require={
        "dev": ["pytest", "mypy", "hypothesis"]
    },
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)
