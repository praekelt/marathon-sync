import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'requirements.txt')) as f:
    requires = filter(None, f.readlines())

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
      author='Jamie Hewland',
      author_email='jhewland@gmail.com',
      url='http://github.com/praekelt/marathon-sync',
      license='BSD',
      keywords='marathon,mesos',
      packages=find_packages(exclude=['docs']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      entry_points={
          'console_scripts': ['marathon-sync = marathon_sync.cli:entry_point'],
      })
