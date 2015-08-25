import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'VERSION')) as f:
    version = f.read().strip()

setup(name='marathon-sync',
      version=version,
      description='Marathon Sync',
      classifiers=[
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='Praekelt Foundation',
      author_email='dev@praekeltfoundation.org',
      url='http://github.com/praekelt/marathon-sync',
      license='BSD',
      keywords='marathon,mesos',
      packages=find_packages(exclude=['docs']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "Twisted",
          "treq",
      ],
      entry_points={
          'console_scripts': ['marathon-sync = marathon_sync.cli:entry_point'],
      })
