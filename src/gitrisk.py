import argparse
import configparser
import sys
import re

class GitRisk:
  mSpecString = None

  def __init__(self, aSpecString):
    self.mSpecString = aSpecString

  def getTicketNamesFromFile(self, aFileName):
    f = open(aFileName)
    results = []
    for line in f:
      result = re.search(self.mSpecString, line)
      results.append(result.group(0))
    return results

def createParser():
  parser = argparse.ArgumentParser(description='''
  Parse git log files for potential regression risks after a merge
  ''', add_help=True)
  parser.add_argument('-c', '--config', dest='confFile', help='Specify a configuration file', action='store')
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

if __name__ == '__main__':
  main()
