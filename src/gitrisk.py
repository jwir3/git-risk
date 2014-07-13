import argparse
import configparser
import sys
import re

class GitRisk:
  mSpecString = None
  mRepoPath = "."

  def __init__(self, aSpecString, repo="."):
    self.mSpecString = aSpecString
    self.mRepoPath = repo

  def getTicketNamesFromFile(self, aFileName):
    f = open(aFileName)
    results = []
    for line in f:
      result = re.search(self.mSpecString, line)
      results.append(result.group(0))
    return results

  def getRepoPath(self):
    return self.mRepoPath

def createParser():
  parser = argparse.ArgumentParser(description='''
  Parse git log files for potential regression risks after a merge
  ''', add_help=True)
  parser.add_argument('-c', '--config', dest='confFile', help='Specify a configuration file', action='store')
  parser.add_argument('-r', '--repository', dest='repo', help='Specify a directory on which to operate', action='store')
  return parser

def main():
  parser = createParser()
  parsedArgs = parser.parse_args(sys.argv[1:])
  if not parsedArgs.confFile:
    parser.print_help()
    return

  repo = '.'
  if parsedArgs.repo:
    repo = parsedArgs.repo

  config = configparser.SafeConfigParser()
  config.read(parsedArgs.confFile)
  searchString = config.get('main', 'ticket-spec')
  gitrisk = GitRisk(searchString, repo=repo)

if __name__ == '__main__':
  main()
