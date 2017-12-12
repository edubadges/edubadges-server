import os
import re

from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()


def dependencies_from_requirements(requirements_filename):
    install_requires = []
    dependency_links = []
    with open(requirements_filename) as fh:
        for line in fh.read().split("\n"):
            line = line.strip()
            if len(line) < 1 or line.startswith('#') or line.startswith('--'):
                continue
            matches = re.match(r'git\+(?P<path>.+/)(?P<package_name>.+)\.git@(?P<version>.+)$', line)
            if matches:
                d = matches.groupdict()
                dependency_links.append("{line}#egg={package_name}-{version}".format(
                    line=line,
                    package_name=d.get('package_name'),
                    version=d.get('version')
                ))
                install_requires.append("{package_name}=={version}".format(**d))
            else:
                install_requires.append(line)
    return install_requires, dependency_links


install_requires, dependency_links = dependencies_from_requirements('requirements.txt')


setup(
    name='badgr-server',
    version='2.0.23',

    package_dir={'': "apps"},
    packages=find_packages('apps'),
    include_package_data=True,

    license='GNU Affero General Public License v3',
    description='Digital badge management for issuers, earners, and consumers',
    long_description=README,
    url='https://badgr.io/',
    author='Concentric Sky',
    author_email='badgr@concentricsky.com',
    install_requires=install_requires,
    dependency_links=dependency_links,

    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Education',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],

)
