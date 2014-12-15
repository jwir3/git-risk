from setuptools import setup
import os
import os.path

progName = 'gitrisk'
progVersion = '0.0.4'
progDescription = 'A tool for determining which tickets included in a merge might be at risk of regressions'
progAuthor = 'Scott Johnson'
progEmail = 'jaywir3@gmail.com'
progUrl = 'http://github.com/jwir3/git-risk'
downloadUrl = 'https://github.com/jwir3/git-risk/archive/gitrisk-v0.0.4.tar.gz'
entryPoints = {
  'console_scripts': [ 'git-risk = gitrisk.gitrisk:main' ]
}

requirements = [
  'configparser>=3.3.0',
  'GitPython>=0.3.2'
]

curDir = os.path.dirname(os.path.realpath(__file__))

setup(name=progName,
      version=progVersion,
      description=progDescription,
      author=progAuthor,
      author_email=progEmail,
      url=progUrl,
      packages=['gitrisk'],
      entry_points=entryPoints,
      test_suite='tests',
      license='Mozilla Public License v2.0',
      install_requires=requirements
)
