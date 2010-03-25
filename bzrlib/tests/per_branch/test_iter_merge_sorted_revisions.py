# Copyright (C) 2009, 2010 Canonical Ltd
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""Tests for Branch.iter_merge_sorted_revisions()"""

from bzrlib import (
    errors,
    revision,
    tests,
    )

from bzrlib.tests import per_branch


class TestIterMergeSortedRevisions(per_branch.TestCaseWithBranch):

    def setUp(self):
        super(TestIterMergeSortedRevisions, self).setUp()
        self.branch = self.make_branch_with_merges('.')

    def make_branch_with_merges(self, relpath):
        try:
            builder = self.make_branch_builder(relpath)
        except (errors.TransportNotPossible, errors.UninitializableFormat):
            raise tests.TestNotApplicable('format not directly constructable')
        builder.start_series()
        builder.build_snapshot('1', None, [
            ('add', ('', 'TREE_ROOT', 'directory', '')),])
        builder.build_snapshot('1.1.1', ['1'], [])
        builder.build_snapshot('2', ['1'], [])
        builder.build_snapshot('3', ['2', '1.1.1'], [])
        builder.finish_series()
        return builder.get_branch()


    def assertIterRevids(self, expected, *args, **kwargs):
        # We don't care about depths and revnos here, only about returning the
        # right revids.
        revids = [ revid for (revid, depth, revno, eom) in
                   self.branch.iter_merge_sorted_revisions(*args, **kwargs)]
        self.assertEqual(expected, revids)

    def test_merge_sorted(self):
        self.assertIterRevids(['3', '1.1.1', '2', '1'])

    def test_merge_sorted_range(self):
        self.assertIterRevids(['1.1.1', '2'],
                              start_revision_id='1.1.1', stop_revision_id='1')

    def test_merge_sorted_range_start_only(self):
        self.assertIterRevids(['1.1.1', '2', '1'],
                              start_revision_id='1.1.1')

    def test_merge_sorted_range_stop_exclude(self):
        self.assertIterRevids(['3', '1.1.1', '2'], stop_revision_id='1')

    def test_merge_sorted_range_stop_include(self):
        self.assertIterRevids(['3', '1.1.1', '2'],
                              stop_revision_id='2', stop_rule='include')

    def test_merge_sorted_range_stop_with_merges(self):
        self.assertIterRevids(['3', '1.1.1'],
                              stop_revision_id='3', stop_rule='with-merges')

    def test_merge_sorted_range_stop_with_merges_can_show_non_parents(self):
        # 1.1.1 gets logged before the end revision is reached.
        # so it is returned even though 1.1.1 is not a parent of 2.
        self.assertIterRevids(['3', '1.1.1', '2'],
                              stop_revision_id='2', stop_rule='with-merges')

    def test_merge_sorted_range_stop_with_merges_ignore_non_parents(self):
        # 2 is not a parent of 1.1.1 so it must not be returned
        self.assertIterRevids(['3', '1.1.1'],
                              stop_revision_id='1.1.1', stop_rule='with-merges')

    def test_merge_sorted_single_stop_exclude(self):
        # from X..X exclusive is an empty result
        self.assertIterRevids([], start_revision_id='3', stop_revision_id='3')

    def test_merge_sorted_single_stop_include(self):
        # from X..X inclusive is [X]
        self.assertIterRevids(['3'],
                              start_revision_id='3', stop_revision_id='3',
                              stop_rule='include')

    def test_merge_sorted_single_stop_with_merges(self):
        self.assertIterRevids(['3', '1.1.1'],
                              start_revision_id='3', stop_revision_id='3',
                              stop_rule='with-merges')

    def test_merge_sorted_forward(self):
        self.assertIterRevids(['1', '2', '1.1.1', '3'], direction='forward')

    def test_merge_sorted_range_forward(self):
        self.assertIterRevids(['2', '1.1.1'],
                              start_revision_id='1.1.1', stop_revision_id='1',
                              direction='forward')

    def test_merge_sorted_range_start_only_forward(self):
        self.assertIterRevids(['1', '2', '1.1.1'],
                              start_revision_id='1.1.1', direction='forward')

    def test_merge_sorted_range_stop_exclude_forward(self):
        self.assertIterRevids(['2', '1.1.1', '3'],
                              stop_revision_id='1', direction='forward')

    def test_merge_sorted_range_stop_include_forward(self):
        self.assertIterRevids(['2', '1.1.1', '3'],
                              stop_revision_id='2', stop_rule='include',
                              direction='forward')

    def test_merge_sorted_range_stop_with_merges_forward(self):
        self.assertIterRevids(['1.1.1', '3'],
                              stop_revision_id='3', stop_rule='with-merges',
                              direction='forward')
