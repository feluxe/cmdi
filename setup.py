from setuptools import setup, find_packages
from buildlib import yaml

with open('README.md') as f:
    long_description = f.read()

config = yaml.loadfile('Project')

setup(
    name=config['public_name'],
    version=config['version'],
    author=config['author'],
    author_email=config['author_email'],
    maintainer=config['maintainer'],
    maintainer_email=config['maintainer_email'],
    url=config['url'],
    description=config['description'],
    long_description_content_type="text/markdown",
    long_description=long_description,
    download_url=config['url'] + '/tarball/' + config['version'],
    license=config['license'],
    keywords=config['keywords'],
    include_package_data=True,
    platforms="",
    classifiers=[],
    install_requires=[''],
    tests_require=[],
    packages=['cmdi'],
    package_dir={"cmdi": "cmdi"},
    package_data={},
    data_files=[],
    entry_points={'console_scripts': [], 'gui_scripts': []}
)
