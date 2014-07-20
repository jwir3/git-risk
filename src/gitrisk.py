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

  def getTicketNamesFromCommit(self, aCommitObj):
    tickets = set()
    commitsWithoutTickets = set()
    commitMessage = aCommitObj.message
    resultFoundForCommit = False
    for line in commitMessage.split("\n"):
      # Find the first instance of the particular ticket
      if len(line.lstrip().rstrip()) != 0:
        result = self.getTicketNamesFromLine(line)
        if result:
          tickets.add(result)
          resultFoundForCommit = True

    if resultFoundForCommit:
      return tickets
    else:
      return None

  def getTicketNamesFromFile(self, aFileName):
    f = open(aFileName)
    results = []
    for line in f:
      if len(line.lstrip().rstrip()) != 0:
        results.append(self.getTicketNamesFromLine(line))

    if self.mDebugMode:
      print("getTicketNamesFromFile: " + str(results))

    return results

  def getTicketNamesFromLine(self, aLine):
    result = re.search(self.mSpecString, aLine)
    if not result and self.mDebugMode:
      print("Line was empty?")
    elif self.mDebugMode:
      print("Result: " + str(result.group(0)))

    # Handle the case where nothing was found in the commit message that
    # matched the specification.
    if not result:
      return None

    return result.group(0).rstrip().lstrip()

  def isMergeCommit(self, aCommitObj):
    return len(aCommitObj.parents) > 1

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
    if self.mDebugMode:
      print("***** findSuspectCommits - commits: " + aCommitObj.hexsha + ", " + aAncestorCommitObj.hexsha)

    commitRange = aAncestorCommitObj.hexsha + ".." + aCommitObj.hexsha
    commitList = [ x for x in self.mRepo.iter_commits(commitRange) ]
    if self.mDebugMode:
      print("Commit range string: " + commitRange)
      print("Commit list prior to appending: " + str(commitList))
    commitList.append(aAncestorCommitObj)
    if self.mDebugMode:
      print("Commit range: " + str(commitList))

    return set(commitList)

  def getAllSuspectCommitsFromMerge(self, shaHash):
    commit = self.getCommitFromHash(shaHash)

    # There should be a commit that exists with this shaHash
    assert commit, "there is no commit with shaHash: " + shaHash

    # The shaHash should also be a merge commit
    assert len(commit.parents) > 1, "commit " + shaHash + " is not a merge commit"

    commitParentShas = [parent.hexsha for parent in commit.parents]

    if self.mDebugMode:
      print("getAllSuspectCommitsFromMerge - parents: " + str(commitParentShas))

    mergeBase = self.getMergeBase(*commitParentShas)
    # This should not be able to happen...
    assert mergeBase != None, "there was no merge base found for the commits"

    suspectCommits = set()
    for parent in commitParentShas:
      singlePathSuspects = self.findSuspectCommits(self.getCommitFromHash(parent), mergeBase)
      suspectCommits = suspectCommits.union(singlePathSuspects)

    # We also need to check this merge commit, in the event that someone added
    # something to the merge that related to a ticket (probably not a good idea,
    # but people are crazy).
    suspectCommits.add(self.getCommitFromHash(shaHash))

    return suspectCommits

  def checkMerge(self, shaHash):
    suspects = self.getAllSuspectCommitsFromMerge(shaHash)

    allTickets = set()
    commitsWithoutTickets = set()
    for suspectCommit in suspects:
      tickets = self.getTicketNamesFromCommit(suspectCommit)
      if not tickets:
        # We didn't find a ticket for this commit. This could be expected, though,
        # if this is a merge commit.
        if not self.isMergeCommit(suspectCommit):
          commitsWithoutTickets.add(suspectCommit)
      else:
        allTickets = allTickets.union(tickets)

    return (allTickets, commitsWithoutTickets)

  def setDebugMode(self, aDebugMode):
    self.mDebugMode = aDebugMode

  def getOneLineCommitMessage(self, aCommitSha):
    return self.mRepo.git.log(aCommitSha, oneline=True, n=1)

def createParser():
  parser = argparse.ArgumentParser(description='''
  Parse git log files for potential regression risks after a merge
  ''', add_help=True)
  parser.add_argument('-c', '--config', dest='confFile', help='Specify a configuration file', action='store')
  parser.add_argument('-r', '--repository', dest='repo', help='Specify a directory on which to operate', action='store', default=".")
  parser.add_argument(dest='mergeCommit', help='Specify an SHA hash for a merge commit for which git-risk should find potential regression sources', action='store', default='HEAD')
  return parser

def main():
  parser = createParser()
  parsedArgs = parser.parse_args(sys.argv[1:])
  if not parsedArgs.confFile or not parsedArgs.mergeCommit:
    parser.print_help()
    return

  repo = '.'
  if parsedArgs.repo:
    repo = parsedArgs.repo

  config = configparser.SafeConfigParser()
  config.read(parsedArgs.confFile)
  searchString = config.get('main', 'ticket-spec')
  gitrisk = GitRisk(searchString, repo=repo)
  (bugs, commitsWithNoTickets) = gitrisk.checkMerge(parsedArgs.mergeCommit)

  outputResults(gitrisk, parsedArgs.mergeCommit, bugs, commitsWithNoTickets)

def outputResults(gitrisk, mergeCommit, bugs, commitsWithNoTickets):
  print("Tickets potentially affected by:")
  onelineMessage = gitrisk.getOneLineCommitMessage(mergeCommit)
  print(onelineMessage + "\n")
  for bug in bugs:
    print(bug)

  if (len(commitsWithNoTickets) > 0):
    print("\nNote: The following commits did not have tickets associated with them (or git-risk\ncouldn't find them), so there might be undocumented issues that have regression(s)\nstemming from these commits' interactions with the merge.\n")
    for commit in commitsWithNoTickets:
      print(gitrisk.getOneLineCommitMessage(commit))

if __name__ == '__main__':
  main()
