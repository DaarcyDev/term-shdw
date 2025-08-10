from setuptools import setup, find_packages

setup(
    name="term-shdw",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "term-shdw=term_shdw.main:main",
        ],
    },
    install_requires=[],
)
