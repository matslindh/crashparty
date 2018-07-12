from setuptools import setup

setup(
    name='crashparty',
    version='0.0.1',
    include_package_data=True,
    install_requires=[
        'flask',
        'flask_sse',
        'memorpy',
        'pypiwin32',
        'WMI',
    ],
)