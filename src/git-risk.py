import argparse
import configparser
import sys
import re

def createParser():
  parser = argparse.ArgumentParser(description='''
    Parse git log files for potential regression risks after a merge
  ''', add_help=True)
  parser.add_argument('-c', '--config', dest='confFile', help='Specify a configuration file', action='store')
  parser.add_argument('-t', '--test', dest='testFile', help='Specify a test file to test against with the given config file', action='store', default=False)
  return parser

def runTestWithFile(aFileName, aRegex):
  f = open(aFileName)
  for line in f:
    result = re.search(aRegex, line)
    print(result.group(0))

def main():
  parser = createParser()
  parsedArgs = parser.parse_args(sys.argv[1:])
  if not parsedArgs.confFile:
    parser.print_help()
    return

  config = configparser.SafeConfigParser()
  config.read(parsedArgs.confFile)
  searchString = config.get('main', 'ticket-spec')
  if parsedArgs.testFile:
      runTestWithFile(parsedArgs.testFile, searchString)

if __name__ == '__main__':
  main()
