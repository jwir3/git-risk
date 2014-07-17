import imp
import unittest
import zipfile
import os.path
import os
import tempfile
import shutil

class TestSpecifications(unittest.TestCase):
  mGitRepoPath = None
  mGitRiskObj = None

  def setUp(self):
    self.mTempDir = tempfile.mkdtemp(prefix='gitRiskTest')
    self.assertTrue(os.path.exists(self.mTempDir))
    zipFh = open('data/testrepo.zip', 'rb')
    testRepoZip = zipfile.ZipFile(zipFh)
    for name in testRepoZip.namelist():
      testRepoZip.extract(name, self.mTempDir)
    zipFh.close()

    # The temp directory should be populated and contain
    # at least a git-risk-info file.
    specString = "^(\W)*([B|b][U|u][G|g])(\ )*(\#)*[0-9]+"
    self.mGitRepoPath = os.path.join(self.mTempDir, 'testrepo')
    self.assertTrue(os.path.exists(os.path.join(self.mGitRepoPath, "git-risk-info")))
    self.mGitRiskModule = imp.load_source('gitrisk', '../gitrisk.py')
    self.mGitRiskObj = self.mGitRiskModule.GitRisk(specString, self.mGitRepoPath, debug=True)

  def tearDown(self):
    shutil.rmtree(self.mTempDir)
    self.assertFalse(os.path.exists(self.mTempDir))

  def test_JMTicketNames(self):
    self.mGitRiskObj = self.mGitRiskModule.GitRisk("(JM|jm)-[0-9]+")
    tickets = self.mGitRiskObj.getTicketNamesFromFile('data/testjmtickets.txt')

    self.assertEqual(os.path.abspath("."), self.mGitRiskObj.getRepoPath())

    # We expect 4 tickets, JM-1966, JM-1726, jm-1922, and jm-1021
    self.assertEqual('JM-1966', tickets[0])
    self.assertEqual('JM-1726', tickets[1])
    self.assertEqual('jm-1922', tickets[2])
    self.assertEqual('jm-1021', tickets[3])

  def test_BugTicketNames(self):
    gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ [0-9]+", os.path.abspath("."), debug=True)

    tickets = gitRisk.getTicketNamesFromFile('data/bugtickets.txt')

    self.assertEqual(os.path.abspath("."), gitRisk.getRepoPath())

    # We expect 9 tickets
    self.assertEqual(9, len(tickets))
    self.assertEqual('Bug 1028867', tickets[0])
    self.assertEqual('Bug 1017835', tickets[1])
    self.assertEqual('Bug 1017835', tickets[2])
    self.assertEqual('bug 1018551', tickets[3])
    self.assertEqual('bug 1018034', tickets[4])
    self.assertEqual('Bug 1029104', tickets[5])
    self.assertEqual('Bug 1029104', tickets[6])
    self.assertEqual('Bug 1029104', tickets[7])
    self.assertEqual('Bug 19283', tickets[8])

  def test_getRepo(self):
    self.assertEqual(self.mGitRepoPath, self.mGitRiskObj.getRepoPath())

  def test_getCommitFromHash(self):
    commit = self.mGitRiskObj.getCommitFromHash('c2a881d')
    self.assertTrue(commit)
    self.assertEqual("c2a881d4c5753a2e6e6e1130d0e27b17a44b4c4c", commit.hexsha)

  def test_getMergeBase(self):
    mergeBaseSingle = self.mGitRiskObj.getMergeBase('c2a881d')
    self.assertEqual("c2a881d4c5753a2e6e6e1130d0e27b17a44b4c4c", mergeBaseSingle.hexsha)

    mergeBaseDual = self.mGitRiskObj.getMergeBase("c2a881d", "6ff4935")
    self.assertEquals("7b9609a1cacce59b81963762f885d7a25453e72e", mergeBaseDual.hexsha)

    mergeBaseTriple1 = self.mGitRiskObj.getMergeBase("c2a881d", "6ff4935", "6a5c798")
    self.assertEquals("7b9609a1cacce59b81963762f885d7a25453e72e", mergeBaseTriple1.hexsha)

    mergeBaseTriple2 = self.mGitRiskObj.getMergeBase("6ff4935", "6a5c798", "88f06c9")
    self.assertEquals("deb5eb357ef6677301b629922279cf2221d4a91d", mergeBaseTriple2.hexsha)

  # def test_checkMerge(self):
  #   self.mGitRiskObj = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ [0-9]+", self.mGitRepoPath, debug=True)
  #   bugs = self.mGitRiskObj.checkMerge("d8bb7b32e43bf27f49a4dc3d27d9f799e829db9d")

  def test_getTicketNamesFromCommit(self):
    commitWithMultipleBugs = self.mGitRiskObj.getCommitFromHash('e4a06631036107e6a2ba5bd9946c20af4f367dff')
    tickets = self.mGitRiskObj.getTicketNamesFromCommit(commitWithMultipleBugs)
    self.assertTrue("Bug #27" in tickets)
    self.assertTrue("Bug #72" in tickets)

    # Now for a more tricky test case. The commit message for this ticket looks like:
    # Bug #98: Replace name 'thingSearcher' accidentally added in bug #72 with 'thingMaker', which better describes the tool.
    # It's expected that the function should return 'Bug #98', but NOT 'bug #72'.
    commitWithTextBugs = self.mGitRiskObj.getCommitFromHash('52f15a65ebf84949bb56df7e7b1be9fb77ee6ce8')
    tickets = self.mGitRiskObj.getTicketNamesFromCommit(commitWithTextBugs)
    self.assertEquals(len(tickets), 1)
    self.assertTrue("Bug #98" in tickets)

    # Let's check a commit that doesn't actually have a ticket associated
    # with it.
    commitWithNoTicket = self.mGitRiskObj.getCommitFromHash("836ceeac65e9e9a4bc1aacf66f08a6ebb209fedb")
    tickets = self.mGitRiskObj.getTicketNamesFromCommit(commitWithNoTicket)
    self.assertFalse(tickets)

    # And, one more test just to make sure that commit messages starting with
    # something other than the spec, but then have an instance of the spec within
    # them aren't highlighted as tickets.
    commitWithNoTicketButMatchingSpec = self.mGitRiskObj.getCommitFromHash("0d75d6c25419313db8c7c85b19a2b7ae2e3020f7")
    tickets = self.mGitRiskObj.getTicketNamesFromCommit(commitWithNoTicketButMatchingSpec)
    self.assertFalse(tickets)

  def test_findSuspectCommits(self):
    suspectCommits = self.mGitRiskObj.findSuspectCommits(self.mGitRiskObj.getCommitFromHash('6a5c7'), self.mGitRiskObj.getCommitFromHash('c2a88'))
    self.assertEquals(len(suspectCommits), 3)

    commitHashes = [x.hexsha for x in suspectCommits]
    self.assertTrue("6a5c7989edfaded4241ea21a742a9b93d5205b47" in commitHashes)
    self.assertTrue("deb5eb357ef6677301b629922279cf2221d4a91d" in commitHashes)
    self.assertTrue("c2a881d4c5753a2e6e6e1130d0e27b17a44b4c4c" in commitHashes)

    complexCommit1 = self.mGitRiskObj.getCommitFromHash('836ceeac65e9e9a4bc1aacf66f08a6ebb209fedb')
    complexCommit2 = self.mGitRiskObj.getCommitFromHash('7b9609a1cacce59b81963762f885d7a25453e72e')
    complexSuspectCommits = self.mGitRiskObj.findSuspectCommits(complexCommit1, complexCommit2)
    expectedCommits = {'836ceeac65e9e9a4bc1aacf66f08a6ebb209fedb',
                       'd8bb7b32e43bf27f49a4dc3d27d9f799e829db9d',
                       'f5813f80a012eabe625ecf12dac9efc3964f2d3d',
                       '6a5c7989edfaded4241ea21a742a9b93d5205b47',
                       'ddcdb34cd3dea82e47c50751d8b9b4b3b8c23e4e',
                       'c2a881d4c5753a2e6e6e1130d0e27b17a44b4c4c',
                       '6ff49357e0f3b9fa991bbd9b42e520f91723436e',
                       '88f06c9cf2c3bccf3df73a6c2bcb8a34549ef20f',
                       '7b9609a1cacce59b81963762f885d7a25453e72e'}
    commitHashes2 = [x.hexsha for x in complexSuspectCommits]
    for commitSha in expectedCommits:
      self.assertTrue(commitSha in commitHashes2)

if __name__ == '__main__':
  unittest.main()
