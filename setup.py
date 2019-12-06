from pathlib import Path

from setuptools import find_packages, setup

with open(Path(__file__).parent / "README.rst", encoding="UTF-8") as fin:
    long_description = fin.read()

setup(
    name="nasty",
    use_scm_version={
        "write_to": "nasty/version.py",
        "write_to_template": '__version__ = "{version}"',
    },
    description="NASTY Advanced Search Tweet Yielder",
    long_description=long_description,
    long_description_content_type="text/x-rst; charset=UTF-8",
    author="Lukas Schmelzeisen",
    author_email="me@lschmelzeisen.com",
    license="Apache License, Version 2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet",
        "Topic :: Scientific/Engineering",
        "Topic :: Sociology",
        "Typing :: Typed",
    ],
    keywords=["python", "twitter", "crawler"],
    packages=find_packages(where=".", exclude=["tests*"]),
    python_requires=">=3.6",
    setup_requires=["setuptools_scm~=3.3"],
    install_requires=["overrides~=2.5", "requests~=2.22", "typing-extensions~=3.7"],
    extras_require={
        "dev": [
            "autoflake~=1.3",
            "black==19.10b0",
            "flake8~=3.7",
            "flake8-bandit~=2.1",
            "flake8-bugbear~=19.8",
            "flake8-builtins~=1.4",
            "flake8-comprehensions~=3.1",
            "flake8-eradicate~=0.2",
            "flake8-print~=3.1",
            "flake8-pyi~=19.3",
            "isort[pipfile,pyproject]~=4.3",
            "licenseheaders~=0.7",
            "mypy~=0.750",
            "pep8-naming~=0.9",
            "pipenv-setup~=2.2",
            "pytest~=5.3",
            "pytest-cov~=2.8",
            "responses~=0.10",
            "twine~=3.1",
            "vulture~=1.2",
        ],
    },
    entry_points={"console_scripts": ["nasty=nasty.cli.main:main"]},
    project_urls={
        "Repository": "https://github.com/lschmelzeisen/nasty",
        "Issue Tracker": "https://github.com/lschmelzeisen/nasty/issues",
    },
)
