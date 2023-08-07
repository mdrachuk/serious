from setuptools import setup, find_packages

import serious


def readme():
    with open('README.md', 'r', encoding='utf8') as f:
        return f.read()


setup(
    name='serious',
    version=serious.__version__,
    packages=find_packages(exclude=("tests*",)),
    package_data={"serious": ["py.typed"]},
    zip_safe=False,
    author='mdrachuk',
    author_email='misha@drach.uk',
    description="Easily serialize dataclasses to and from JSON",
    long_description=readme(),
    long_description_content_type='text/markdown',
    url="https://github.com/mdrachuk/serious",
    license="MIT",
    keywords="dataclasses json serialization",
    python_requires=">=3.10",
    project_urls={
        'Pipelines': 'https://dev.azure.com/misha-drachuk/serious',
        'Source': 'https://github.com/mdrachuk/serious/',
        'Issues': 'https://github.com/mdrachuk/serious/issues',
    },
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Utilities",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Typing :: Typed",
    ],
)
