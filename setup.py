#!/usr/bin/env python
from distutils.core import setup

bzr_plugin_name = 'grep'

bzr_plugin_version = (0, 3, 0, 'final', 0)

bzr_commands = ['grep']

if __name__ == '__main__':
    setup(name="bzr grep",
          version="0.3",
          description="Print lines matching pattern for specified "
                      "files and revisions",
          author="Canonical Ltd",
          author_email="bazaar@lists.canonical.com",
          license = "GNU GPL v2",
          url="https://launchpad.net/bzr-grep",
          packages=['bzrlib.plugins.grep'],
          package_dir={'bzrlib.plugins.grep': '.'})
