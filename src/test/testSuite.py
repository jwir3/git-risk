import imp
import unittest
import zipfile
import os.path
import os
import tempfile
import shutil

class TestSpecifications(unittest.TestCase):
  mGitRepoPath = None

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
    self.mGitRepoPath = os.path.join(self.mTempDir, 'testrepo')
    self.assertTrue(os.path.exists(os.path.join(self.mGitRepoPath, "git-risk-info")))
    self.mGitRiskModule = imp.load_source('gitrisk', '../gitrisk.py')

  def tearDown(self):
    shutil.rmtree(self.mTempDir)
    self.assertFalse(os.path.exists(self.mTempDir))

  def test_JMTicketNames(self):
    gitRisk = self.mGitRiskModule.GitRisk("(JM|jm)-[0-9]+")
    tickets = gitRisk.getTicketNamesFromFile('data/testjmtickets.txt')

    self.assertEqual(os.path.abspath("."), gitRisk.getRepoPath())

    # We expect 4 tickets, JM-1966, JM-1726, jm-1922, and jm-1021
    self.assertEqual('JM-1966', tickets[0])
    self.assertEqual('JM-1726', tickets[1])
    self.assertEqual('jm-1922', tickets[2])
    self.assertEqual('jm-1021', tickets[3])

  def test_BugTicketNames(self):
    print("Starting test_BugTicketNames")
    gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ [0-9]+", debug=True)
    tickets = gitRisk.getTicketNamesFromFile('data/bugtickets.txt')

    self.assertEqual(os.path.abspath("."), gitRisk.getRepoPath())

    # We expect 8 tickets
    self.assertEqual(8, len(tickets))
    self.assertEqual('Bug 1028867', tickets[0])
    self.assertEqual('Bug 1017835', tickets[1])
    self.assertEqual('Bug 1017835', tickets[2])
    self.assertEqual('bug 1018551', tickets[3])
    self.assertEqual('bug 1018034', tickets[4])
    self.assertEqual('Bug 1029104', tickets[5])
    self.assertEqual('Bug 1029104', tickets[6])
    self.assertEqual('Bug 1029104', tickets[7])

  def test_getRepo(self):
    gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ [0-9]+", self.mGitRepoPath)
    self.assertEqual(self.mGitRepoPath, gitRisk.getRepoPath())

  def test_getCommitFromHash(self):
    gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ [0-9]+", self.mGitRepoPath)
    commit = gitRisk.getCommitFromHash('c2a881d')
    self.assertTrue(commit)
    self.assertEqual("c2a881d4c5753a2e6e6e1130d0e27b17a44b4c4c", commit.hexsha)

  def test_getMergeBase(self):
    gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ [0-9]+", self.mGitRepoPath)

    mergeBaseSingle = gitRisk.getMergeBase('c2a881d')
    self.assertEqual("c2a881d4c5753a2e6e6e1130d0e27b17a44b4c4c", mergeBaseSingle.hexsha)

    mergeBaseDual = gitRisk.getMergeBase("c2a881d", "6ff4935")
    self.assertEquals("7b9609a1cacce59b81963762f885d7a25453e72e", mergeBaseDual.hexsha)

    mergeBaseTriple1 = gitRisk.getMergeBase("c2a881d", "6ff4935", "6a5c798")
    self.assertEquals("7b9609a1cacce59b81963762f885d7a25453e72e", mergeBaseTriple1.hexsha)

    mergeBaseTriple2 = gitRisk.getMergeBase("6ff4935", "6a5c798", "88f06c9")
    self.assertEquals("deb5eb357ef6677301b629922279cf2221d4a91d", mergeBaseTriple2.hexsha)

  # def test_checkMerge(self):
  #   gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ [0-9]+", self.mGitRepoPath, debug=True)
  #   bugs = gitRisk.checkMerge("d8bb7b32e43bf27f49a4dc3d27d9f799e829db9d")

  def test_getTicketNamesFromCommit(self):
    gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ \#*[0-9]+", self.mGitRepoPath, debug=True)
    commitWithMultipleBugs = gitRisk.getCommitFromHash('e4a06631036107e6a2ba5bd9946c20af4f367dff')
    (tickets,commitsWithoutTickets) = gitRisk.getTicketNamesFromCommit(commitWithMultipleBugs)
    self.assertTrue("Bug #27" in tickets)
    self.assertTrue("Bug #72" in tickets)
    self.assertEquals(len(commitsWithoutTickets), 0)

  def test_findSuspectCommits(self):
    gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ (\#)*[0-9]+", self.mGitRepoPath, debug=True)
    suspectCommits = gitRisk.findSuspectCommits(gitRisk.getCommitFromHash('6a5c7'), gitRisk.getCommitFromHash('c2a88'))
    self.assertEquals(len(suspectCommits), 3)

    commitHashes = [x.hexsha for x in suspectCommits]
    self.assertTrue("6a5c7989edfaded4241ea21a742a9b93d5205b47" in commitHashes)
    self.assertTrue("deb5eb357ef6677301b629922279cf2221d4a91d" in commitHashes)
    self.assertTrue("c2a881d4c5753a2e6e6e1130d0e27b17a44b4c4c" in commitHashes)

    complexCommit1 = gitRisk.getCommitFromHash('836ceeac65e9e9a4bc1aacf66f08a6ebb209fedb')
    complexCommit2 = gitRisk.getCommitFromHash('7b9609a1cacce59b81963762f885d7a25453e72e')
    complexSuspectCommits = gitRisk.findSuspectCommits(complexCommit1, complexCommit2)
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
