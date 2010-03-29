# Copyright (C) 2010 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""Print lines matching PATTERN for specified files and revisions."""

import os
import sys

from bzrlib import errors
from bzrlib.commands import Command, register_command, display_command
from bzrlib.option import Option, ListOption

from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
import re

import grep

import bzrlib
from bzrlib.revisionspec import RevisionSpec
from bzrlib import (
    osutils,
    bzrdir,
    trace,
    )
""")

version_info = (0, 2, 0, 'dev', 0)

# FIXME: _parse_levels should be shared with bzrlib.builtins. this is a copy
# to avoid the error
#   "IllegalUseOfScopeReplacer: ScopeReplacer object '_parse_levels' was used
#   incorrectly: Object already cleaned up, did you assign it to another
#   variable?: _factory
# with lazy import
def _parse_levels(s):
    try:
        return int(s)
    except ValueError:
        msg = "The levels argument must be an integer."
        raise errors.BzrCommandError(msg)


class cmd_grep(Command):
    """Print lines matching PATTERN for specified files and revisions.

    This command searches the specified files and revisions for a given
    pattern.  The pattern is specified as a Python regular expressions[1].

    If the file name is not specified, the revisions starting with the
    current directory are searched recursively. If the revision number is
    not specified, the working copy is searched. To search the last committed
    revision, use the '-r -1' or '-r last:1' option.

    Unversioned files are not searched unless explicitly specified on the
    command line. Unversioned directores are not searched.

    When searching a pattern, the output is shown in the 'filepath:string'
    format. If a revision is explicitly searched, the output is shown as
    'filepath~N:string', where N is the revision number.

    --include and --exclude options can be used to search only (or exclude
    from search) files with base name matches the specified Unix style GLOB
    pattern.  The GLOB pattern an use *, ?, and [...] as wildcards, and \\
    to quote wildcard or backslash character literally. Note that the glob
    pattern is not a regular expression.

    [1] http://docs.python.org/library/re.html#regular-expression-syntax
    """

    encoding_type = 'replace'
    takes_args = ['pattern', 'path*']
    takes_options = [
        'verbose',
        'revision',
        ListOption('exclude', type=str, argname='glob', short_name='X',
            help="Skip files whose base name matches GLOB."),
        ListOption('include', type=str, argname='glob', short_name='I',
            help="Search only files whose base name matches GLOB."),
        Option('files-with-matches', short_name='l',
               help='Print only the name of each input file in '
               'which PATTERN is found.'),
        Option('files-without-match', short_name='L',
               help='Print only the name of each input file in '
               'which PATTERN is not found.'),
        Option('fixed-string', short_name='F',
               help='Interpret PATTERN is a single fixed string (not regex).'),
        Option('from-root',
               help='Search for pattern starting from the root of the branch. '
               '(implies --recursive)'),
        Option('ignore-case', short_name='i',
               help='ignore case distinctions while matching.'),
        Option('levels',
           help='Number of levels to display - 0 for all, 1 for collapsed '
           '(1 is default).',
           argname='N',
           type=_parse_levels),
        Option('line-number', short_name='n',
               help='show 1-based line number.'),
        Option('no-recursive',
               help="Don't recurse into subdirectories. (default is --recursive)"),
        Option('null', short_name='Z',
               help='Write an ASCII NUL (\\0) separator '
               'between output lines rather than a newline.'),
        ]


    @display_command
    def run(self, verbose=False, ignore_case=False, no_recursive=False,
            from_root=False, null=False, levels=None, line_number=False,
            path_list=None, revision=None, pattern=None, include=None,
            exclude=None, fixed_string=False, files_with_matches=False,
            files_without_match=False):

        recursive = not no_recursive

        if levels==None:
            levels=1

        if path_list == None:
            path_list = ['.']
        else:
            if from_root:
                raise errors.BzrCommandError('cannot specify both --from-root and PATH.')

        if files_with_matches and files_without_match:
            raise errors.BzrCommandError('cannot specify both '
                '-l/--files-with-matches and -L/--files-without-matches.')

        print_revno = False
        if revision != None or levels == 0:
            # print revision numbers as we may be showing multiple revisions
            print_revno = True

        eol_marker = '\n'
        if null:
            eol_marker = '\0'

        # if the pattern isalnum, implicitly switch to fixed_string for faster grep
        if grep.is_fixed_string(pattern):
            fixed_string = True

        patternc = None
        if not fixed_string:
            re_flags = 0
            if ignore_case:
                re_flags = re.IGNORECASE
            patternc = grep.compile_pattern(pattern, re_flags)

        if revision == None:
            grep.workingtree_grep(pattern, patternc, path_list, recursive,
                line_number, from_root, eol_marker, include, exclude,
                verbose, fixed_string, ignore_case, files_with_matches,
                files_without_match, self.outf)
        else:
            grep.versioned_grep(revision, pattern, patternc, path_list,
                recursive, line_number, from_root, eol_marker,
                print_revno, levels, include, exclude, verbose,
                fixed_string, ignore_case, files_with_matches,
                files_without_match, self.outf)


register_command(cmd_grep)

def test_suite():
    from bzrlib.tests import TestUtil

    suite = TestUtil.TestSuite()
    loader = TestUtil.TestLoader()
    testmod_names = [
        'test_grep',
        ]

    suite.addTest(loader.loadTestsFromModuleNames(
            ["%s.%s" % (__name__, tmn) for tmn in testmod_names]))
    return suite

