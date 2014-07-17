import argparse
import configparser
import sys
import re
import os
import os.path
from git import *

class GitRisk:
  mSpecString = None
  mRepoPath = "."
  mRepo = None
  mDebugMode = False

  def __init__(self, aSpecString, repo=".", debug=False):
    self.mSpecString = aSpecString
    self.mRepoPath = repo
    self.mDebugMode = debug
    self.mRepo = Repo(self.mRepoPath)

  def getTicketNamesFromFile(self, aFileName):
    f = open(aFileName)
    results = []
    for line in f:
      result = re.search(self.mSpecString, line)
      results.append(result.group(0))
    return results

  def getRepoPath(self):
    return os.path.abspath(self.mRepoPath)

  def getCommitFromHash(self, commitHash):
    if (self.mDebugMode):
      print("Commit hash: " + str(commitHash))

    commit = self.mRepo.commit(commitHash)
    return commit

  def getMergeBase(self, *commitHashes):
    assert type(commitHashes) is tuple, 'commitHashes should be passed as a tuple'

    if (self.mDebugMode):
      print("Type of commitHashes is: " + str(type(commitHashes)))

    # If we don't have any commits, then we can't get the
    # merge base.
    if len(commitHashes) == 0:
      return None

    # If there's only one commit, then it's its own merge base.
    if len(commitHashes) == 1:
      (commitHash,) = commitHashes
      return self.getCommitFromHash(commitHash)

    # If there are exactly two commits, then we use git-merge in the
    # normal way.
    if len(commitHashes) == 2:
      output = self.mRepo.git.merge_base(commitHashes)
    else:
      # If there are more than two commits, then we want to find the
      # octopus merge base because we don't want to consider a hypothetical
      # merge base (we're being conservative)
      output = self.mRepo.git.merge_base(commitHashes, octopus=True)

    return self.getCommitFromHash(output)

  def findSuspectCommits(self, aCommitObj, aAncestorCommitObj):
    commitRange = aAncestorCommitObj.hexsha + ".." + aCommitObj.hexsha
    commitList = [ x for x in self.mRepo.iter_commits(commitRange) ]
    if self.mDebugMode:
      print("Commit range string: " + commitRange)
      print("Commit list prior to appending: " + str(commitList))
    commitList.append(aAncestorCommitObj)
    if self.mDebugMode:
      print("Commit range: " + str(commitList))

    return set(commitList)

  def checkMerge(self, shaHash):
    commit = self.getCommitFromHash(shaHash)

    # There should be a commit that exists with this shaHash
    assert commit, "there is no commit with shaHash: " + shaHash

    # The shaHash should also be a merge commit
    assert len(commit.parents) > 1, "commit " + shaHash + " is not a merge commit"

    commitParentShas = [parent.hexsha for parent in commit.parents]
    if (self.mDebugMode):
      print("commitParentShas: " + str(commitParentShas))

    mergeBase = self.getMergeBase(*commitParentShas)
    # This should not be able to happen...
    assert mergeBase != None, "there was no merge base found for the commits"

    suspectCommits = []
    for parent in commitParentShas:
      singlePathSuspects = self.findSuspectCommits(self.getCommitFromHash(parent), mergeBase)
      suspectCommits = suspectCommits + list(set(singlePathSuspects) - set(suspectCommits))

    return None

def createParser():
  parser = argparse.ArgumentParser(description='''
  Parse git log files for potential regression risks after a merge
  ''', add_help=True)
  parser.add_argument('-c', '--config', dest='confFile', help='Specify a configuration file', action='store')
  parser.add_argument('-r', '--repository', dest='repo', help='Specify a directory on which to operate', action='store', default=".")
  parser.add_argument('-m', '--merge', dest='mergeCommit', help='Specify an SHA hash for a merge commit for which git-risk should find potential regression sources', action='store', default='HEAD')
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
  bugs = gitrisk.checkMerge(parser.mergeCommit)

if __name__ == '__main__':
  main()
