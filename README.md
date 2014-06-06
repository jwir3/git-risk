git-risk
=====================

A script that allows users of git to determine which ticket(s) included in a merge might be at risk of regressions.

Usage
---------------------
`git-risk` assumes that you have certain data about a series of commits in
`git`. The best way to obtain this information is to run `git-risk` as a hook
within `git` itself. `git-risk` can, however, be run as a standalone application
from the command line. Both methods are described below.

Command-Line Usage
---------------------
