import argparse
import configparser
import sys
import re
import os
import os.path
import pkg_resources
from git import *

class GitRisk:
  mSpecString = None
  mRepoPath = "."
  mRepo = None
  mDebugMode = False
  mQuietMode = False

  def __init__(self, aSpecString=None, repo=".", debug=False, quiet=False):

    self.mRepoPath = repo
    self.mDebugMode = debug
    self.mRepo = Repo(self.mRepoPath)
    self.mQuietMode = quiet
    self.mRegexGroup = 0

    if not aSpecString:
      configReader = self.mRepo.config_reader()

      if not configReader.has_section('gitrisk'):
        print "A `gitrisk` section was not found in the git configuration for this repository. You will need to add one."
        sys.exit(1)

      if not configReader.has_option('gitrisk', 'ticketRegex'):
        print "A `ticketRegex` option was not found in the git configuration for this repository. You will need to add one to the `gitrisk` section."
        sys.exit(1)

      if configReader.has_option('gitrisk', 'ticketNumberRegexGroup'):
          self.mRegexGroup = configReader.get_value('gitrisk', 'ticketNumberRegexGroup')

      self.mSpecString = configReader.get_value('gitrisk', 'ticketRegex')

      self.mSpecString = self.mSpecString.decode('string-escape')
      self.mSpecString = self.mSpecString.replace('"', '')
      if not self.mSpecString:
        raise Exception("Unable to find a regular expression for searching tickets")
    else:
      self.mSpecString = aSpecString

  def isInQuietMode(self):
    return self.mQuietMode

  def setInQuietMode(self, aQuiet):
    self.mQuietMode = aQuiet

  def getTicketRegex(self):
    return self.mSpecString

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
    if self.mDebugMode:
      print("***** DEBUG: Spec String: " + self.mSpecString)
      print("***** DEBUG: aLine: " + aLine)
      print("***** DEBUG: ticket group: " + str(self.mRegexGroup))

    result = re.search(self.mSpecString, aLine)
    if not result and self.mDebugMode:
      print("***** DEBUG: Line was empty")
    elif self.mDebugMode:
      print("***** DEBUG: Result: " + str(result.group(self.mRegexGroup)))

    # Handle the case where nothing was found in the commit message that
    # matched the specification.
    if not result:
      return None

    return result.group(self.mRegexGroup).rstrip().lstrip()

  def isMergeCommit(self, aCommit):
    if (type(aCommit) is str):
      commit = self.getCommitFromHash(aCommit)
    else:
      commit = aCommit

    return len(commit.parents) > 1

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
    assert mergeBase, "there was no merge base found for the commits"

    suspectCommits = set()
    for parent in commitParentShas:
      singlePathSuspects = self.findSuspectCommits(self.getCommitFromHash(parent), mergeBase)
      suspectCommits = suspectCommits.union(singlePathSuspects)

    # We also need to check this merge commit, in the event that someone added
    # something to the merge that related to a ticket (probably not a good idea,
    # but people are crazy).
    suspectCommits.add(self.getCommitFromHash(shaHash))

    return suspectCommits

  def getAllSuspectCommitsInRange(self, aFromHash, aToHash):
    commitFrom = self.getCommitFromHash(aFromHash)
    commitTo = self.getCommitFromHash(aToHash)

    # There should be a commit that exists with these hashes
    assert commitFrom, "there is no commit with shaHash: " + aFromHash
    assert commitTo, "there is no commit with shaHash: " + aToHash

    initialRange = [commitFrom, commitTo]

    mergeBase = self.getMergeBase(*initialRange)

    # This should not be able to happen...
    assert mergeBase, "there was no merge base found for the commits"

    suspectCommits = set()
    for commit in initialRange:
      singlePathSuspects = self.findSuspectCommits(self.getCommitFromHash(commit), mergeBase)
      suspectCommits = suspectCommits.union(singlePathSuspects)

    return suspectCommits

  def checkCommitRange(self, aStartCommit, aEndCommit):
      suspects = self.getAllSuspectCommitsInRange(aStartCommit, aEndCommit)
      return self._checkSuspectCommits(suspects)

  def checkMerge(self, shaHash):
    if self.mDebugMode:
      print("****** TICKET SPEC Ticket Spec String: " + str(self.getTicketRegex()))

    suspects = self.getAllSuspectCommitsFromMerge(shaHash)
    return self._checkSuspectCommits(suspects)


  def _checkSuspectCommits(self, aSuspects):
    allTickets = set()
    commitsWithoutTickets = set()
    for suspectCommit in aSuspects:
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

  def outputResults(self, commitHash, bugs, commitsWithNoTickets):
    if not self.isInQuietMode():
      print("Tickets potentially affected by:")
      onelineMessage = self.getOneLineCommitMessage(commitHash)
      print(onelineMessage + "\n")
    for bug in bugs:
      print(bug)

    if not self.isInQuietMode():
      if (len(commitsWithNoTickets) > 0):
        print("\nNote: The following commits did not have tickets associated with them (or git-risk\ncouldn't find them), so there might be undocumented issues that have regression(s)\nstemming from these commits' interactions with the merge.\n")
        for commit in commitsWithNoTickets:
          print(self.getOneLineCommitMessage(commit))

def createParser():
  version = pkg_resources.require('gitrisk')[0].version
  parser = argparse.ArgumentParser(description='''
  Parse git log files for potential regression risks in a given range or after a merge
  ''', add_help=True)
  parser.add_argument('-f', '--config-file', dest='confFile', help='Specify a configuration file', action='store')
  parser.add_argument('-r', '--repository', dest='repo', help='Specify a directory on which to operate', action='store', default=".")
  parser.add_argument('-q', '--quiet', dest='quietMode', help='Make git-risk use "quiet" mode, which means only the appropriate ticket(s) will be output.', action='store_true', default=False)
  parser.add_argument('-g', '--debug', dest='debugMode', help="Make git-risk print out debugging information", action='store_true', default=False)
  parser.add_argument('-v', '--version', help='Display the version information for git-risk', action='version', version='git-risk version ' + str(version))
  parser.add_argument('-c', '--commit', metavar='<commit-hash>', dest='commitHash', help='Specify an SHA hash for a commit on which to operate.', action='store', default='HEAD')
  return parser

def printVersion():
  version = pkg_resources.require('gitrisk')[0].version
  print("git-risk version " + str(version))

def main():
  parser = createParser()
  parsedArgs = parser.parse_args(sys.argv[1:])

  if not parsedArgs.commitHash:
    printVersion()
    parser.print_help()
    return 1

  repo = '.'
  if parsedArgs.repo:
    repo = parsedArgs.repo

  if parsedArgs.confFile:
    config = configparser.SafeConfigParser()
    config.read(parsedArgs.confFile)
    searchString = config.get('main', 'ticket-spec')
    gitrisk = GitRisk(searchString, repo=repo, quiet=parsedArgs.quietMode, debug=parsedArgs.debugMode)
  else:
    # try:
      gitrisk = GitRisk(repo=repo, quiet=parsedArgs.quietMode, debug=parsedArgs.debugMode)
    # except:
      # parser.print_help()
      # return 1

  # If the commit given on the command line is a merge commit, then we'll check
  # the merge. Otherwise, we'll check for a range HEAD..<commit>
  if gitrisk.isMergeCommit(parsedArgs.commitHash):
      (bugs, commitsWithNoTickets) = gitrisk.checkMerge(parsedArgs.commitHash)
  else:
      (bugs, commitsWithNoTickets) = gitrisk.checkCommitRange('HEAD', parsedArgs.commitHash)

  gitrisk.outputResults(parsedArgs.commitHash, bugs, commitsWithNoTickets)
  return 0

if __name__ == '__main__':
  exit(main())
