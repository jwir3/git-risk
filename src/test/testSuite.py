import imp
import unittest

class TestSpecifications(unittest.TestCase):
  def setUp(self):
    self.mGitRiskModule = imp.load_source('gitrisk', '../gitrisk.py')

  def test_JMTicketNames(self):
    gitRisk = self.mGitRiskModule.GitRisk("(JM|jm)-[0-9]+")
    tickets = gitRisk.getTicketNamesFromFile('data/testjmtickets.txt')

    # We expect 4 tickets, JM-1966, JM-1726, jm-1922, and jm-1021
    self.assertEqual('JM-1966', tickets[0])
    self.assertEqual('JM-1726', tickets[1])
    self.assertEqual('jm-1922', tickets[2])
    self.assertEqual('jm-1021', tickets[3])

if __name__ == '__main__':
  unittest.main()
