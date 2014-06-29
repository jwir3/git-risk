import argparse
import configparser
import sys
import re

class GitRisk:
  mSpecString = None

  def __init__(self, aSpecString):
    self.mSpecString = aSpecString

  def _runTestWithFile(self, aFileName):
    f = open(aFileName)
    for line in f:
      result = re.search(self.mSpecString, line)
      print(result.group(0))

def createParser():
  parser = argparse.ArgumentParser(description='''
  Parse git log files for potential regression risks after a merge
  ''', add_help=True)
  parser.add_argument('-c', '--config', dest='confFile', help='Specify a configuration file', action='store')
  parser.add_argument('-t', '--test', dest='testFile', help='Specify a test file to test against with the given config file', action='store', default=False)
  return parser

def main():
  parser = createParser()
  parsedArgs = parser.parse_args(sys.argv[1:])
  if not parsedArgs.confFile:
    parser.print_help()
    return

  config = configparser.SafeConfigParser()
  config.read(parsedArgs.confFile)
  searchString = config.get('main', 'ticket-spec')
  gitrisk = GitRisk(searchString)
  if parsedArgs.testFile:
      gitrisk._runTestWithFile(parsedArgs.testFile)

if __name__ == '__main__':
  main()
