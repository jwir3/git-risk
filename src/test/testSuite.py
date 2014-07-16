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
    gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ [0-9]+")
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

if __name__ == '__main__':
  unittest.main()
