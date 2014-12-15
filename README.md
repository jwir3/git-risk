git-risk
=====================

* [![PyPI version](https://badge.fury.io/py/gitrisk.svg)](http://badge.fury.io/py/gitrisk)
* [![Build Status](https://travis-ci.org/jwir3/git-risk.svg)](https://travis-ci.org/jwir3/git-risk)

A script that allows users of git to determine which ticket(s) included in a merge might be at risk of regressions.

Usage
---------------------
`git-risk` assumes that you have certain data about a series of commits in
`git`. The best way to obtain this information is to run `git-risk` as a hook
within `git` itself. `git-risk` can, however, be run as a standalone application
from the command line. Both methods are described below.

###Command-Line Usage
`git-risk [-qm] <merge-commit hash>`

Where:
* `<merge-commit hash>` is an SHA hash that was a merge commit
* `-q`: Flag used to indicate that "quiet" mode should be used, which means only
        the appropriate ticket(s) will be output.
* `-m`: Flag used to indicate that `git-risk` should quickly return a "positive"
        status when run on a commit that isn't a merge commit (used in conjunction
        with the git hook(s) described below).

The output of this command will give you a series of tickets/issues/bugs that
can be checked for regressions:

_Example (Taken from test repository included in test data/ directory):_
```
$ git-risk ddcdb34
Tickets potentially affected by:
ddcdb34 Merge branch 'bug-14'

Bug #14
Bug #0

Note: The following commits did not have tickets associated with them (or git-risk
couldn't find them), so there might be undocumented issues that have regression(s)
stemming from these commits' interactions with the merge.

c2a881d (No Ticket): Added git-risk-info and renamed README.txt to README.md.
```

If the `-q` option had been specified, the output would look more like:
```bash
$ git-risk -q ddcdb34
Bug #14
Bug #0
```

Note that with the `-q` option, the commit(s) where no ticket was found are not
shown. This can potentially lead to problems where regression sources can be
masked, so use with caution.

###Hook-based Usage:
You can run `git-risk` within any hook inside of `git` once a commit is created.
This essentially means that only the `pre-commit` hook can't be used (for the
time being) with `git-risk`. The most logical place to use `git-risk` is the
`post-commit` hook, which you can setup in the following way:

1. Edit `.git/hooks/pre-commit` in your source folder (or globally, if you wish
   to enable it for all git repositories on your local machine).
2. Add the following line to `.git/hooks/pre-commit`:
```
   git-risk -m `git rev-list -1 HEAD`
```

That's it! The `-m` option is only to specify that a 'pass' result should be
returned if the commit in question isn't a merge commit (since git-risk can't
automatically detect issues likely to be affected by a non-merge commit.
