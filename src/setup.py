from setuptools import setup
import os

entryPoints = {'console_scripts': [ 'git-risk = gitrisk:main' ] }

setup(name='git-risk',
      version='0.0.3',
      description='A script that allows users of git to determine which ticket(s) included in a merge might be at risk of regressions.',
      author='Scott Johnson',
      author_email='jaywir3@gmail.com',
      url='http://github.com/jwir3/git-risk',
      entry_points=entryPoints,
      py_modules=['gitrisk']
)
