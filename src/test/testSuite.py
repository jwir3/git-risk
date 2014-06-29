import imp
import unittest
import zipfile
import os.path
import os
import tempfile
import shutil

class TestSpecifications(unittest.TestCase):
  def setUp(self):
    self.mTempDir = tempfile.mkdtemp(prefix='gitRiskTest')
    self.assertTrue(os.path.exists(self.mTempDir))
    zipFh = open('data/testRepo.zip', 'rb')
    testRepoZip = zipfile.ZipFile(zipFh)
    for name in testRepoZip.namelist():
      testRepoZip.extract(name, self.mTempDir)
    zipFh.close()

    # The temp directory should be populated and contain
    # at least a git-risk-info file.
    pathToTestRepo = os.path.join(self.mTempDir, 'testRepo')
    self.assertTrue(os.path.exists(os.path.join(pathToTestRepo, "git-risk-info")))
    self.mGitRiskModule = imp.load_source('gitrisk', '../gitrisk.py')

  def tearDown(self):
    shutil.rmtree(self.mTempDir)
    self.assertFalse(os.path.exists(self.mTempDir))

  def test_JMTicketNames(self):
    gitRisk = self.mGitRiskModule.GitRisk("(JM|jm)-[0-9]+")
    tickets = gitRisk.getTicketNamesFromFile('data/testjmtickets.txt')

    # We expect 4 tickets, JM-1966, JM-1726, jm-1922, and jm-1021
    self.assertEqual('JM-1966', tickets[0])
    self.assertEqual('JM-1726', tickets[1])
    self.assertEqual('jm-1922', tickets[2])
    self.assertEqual('jm-1021', tickets[3])

  def test_BugTicketNames(self):
    gitRisk = self.mGitRiskModule.GitRisk("([B|b][U|u][G|g])\ [0-9]+")
    tickets = gitRisk.getTicketNamesFromFile('data/bugtickets.txt')

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

if __name__ == '__main__':
  unittest.main()
