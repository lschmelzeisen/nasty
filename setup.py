from setuptools import setup

setup(
    use_scm_version={
        "write_to": "nasty/version.py",
        "write_to_template": '__version__ = "{version}"\n',
    },
)
