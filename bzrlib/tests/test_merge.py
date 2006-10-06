# Copyright (C) 2005, 2006 by Canonical Ltd
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

import os
from StringIO import StringIO

from bzrlib import conflicts
from bzrlib.branch import Branch
from bzrlib.builtins import merge
from bzrlib.conflicts import ConflictList, TextConflict
from bzrlib.errors import UnrelatedBranches, NoCommits, BzrCommandError
from bzrlib.merge import transform_tree, merge_inner
from bzrlib.osutils import pathjoin
from bzrlib.revision import common_ancestor
from bzrlib.tests import TestCaseWithTransport
from bzrlib.trace import (enable_test_log, disable_test_log)
from bzrlib.workingtree import WorkingTree


class TestMerge(TestCaseWithTransport):
    """Test appending more than one revision"""

    def test_pending(self):
        wt = self.make_branch_and_tree('.')
        rev_a = wt.commit("lala!")
        self.assertEqual([rev_a], wt.get_parent_ids())
        merge([u'.', -1], [None, None])
        self.assertEqual([rev_a], wt.get_parent_ids())

    def test_undo(self):
        wt = self.make_branch_and_tree('.')
        wt.commit("lala!")
        wt.commit("haha!")
        wt.commit("blabla!")
        merge([u'.', 2], [u'.', 1])

    def test_nocommits(self):
        self.test_pending()
        wt2 = self.make_branch_and_tree('branch2')
        self.assertRaises(NoCommits, merge, ['branch2', -1], 
                          [None, None])
        return wt2

    def test_unrelated(self):
        wt2 = self.test_nocommits()
        wt2.commit("blah")
        self.assertRaises(UnrelatedBranches, merge, ['branch2', -1], 
                          [None, None])
        return wt2

    def test_merge_one_file(self):
        """Do a partial merge of a tree which should not affect tree parents."""
        wt1 = self.make_branch_and_tree('branch1')
        tip = wt1.commit('empty commit')
        wt2 = self.make_branch_and_tree('branch2')
        wt2.pull(wt1.branch)
        file('branch1/foo', 'wb').write('foo')
        file('branch1/bar', 'wb').write('bar')
        wt1.add('foo')
        wt1.add('bar')
        wt1.commit('add foobar')
        os.chdir('branch2')
        self.run_bzr('merge', '../branch1/baz', retcode=3)
        self.run_bzr('merge', '../branch1/foo')
        self.failUnlessExists('foo')
        self.failIfExists('bar')
        wt2 = WorkingTree.open('.') # opens branch2
        self.assertEqual([tip], wt2.get_parent_ids())
        
    def test_pending_with_null(self):
        """When base is forced to revno 0, parent_ids are set"""
        wt2 = self.test_unrelated()
        wt1 = WorkingTree.open('.')
        br1 = wt1.branch
        br1.fetch(wt2.branch)
        # merge all of branch 2 into branch 1 even though they 
        # are not related.
        self.assertRaises(BzrCommandError, merge, ['branch2', -1],
                          ['branch2', 0], reprocess=True, show_base=True)
        merge(['branch2', -1], ['branch2', 0], reprocess=True)
        self.assertEqual([br1.last_revision(), wt2.branch.last_revision()],
            wt1.get_parent_ids())
        return (wt1, wt2.branch)

    def test_two_roots(self):
        """Merge base is sane when two unrelated branches are merged"""
        wt1, br2 = self.test_pending_with_null()
        wt1.commit("blah")
        last = wt1.branch.last_revision()
        self.assertEqual(common_ancestor(last, last, wt1.branch.repository), last)

    def test_create_rename(self):
        """Rename an inventory entry while creating the file"""
        tree =self.make_branch_and_tree('.')
        file('name1', 'wb').write('Hello')
        tree.add('name1')
        tree.commit(message="hello")
        tree.rename_one('name1', 'name2')
        os.unlink('name2')
        transform_tree(tree, tree.branch.basis_tree())

    def test_layered_rename(self):
        """Rename both child and parent at same time"""
        tree =self.make_branch_and_tree('.')
        os.mkdir('dirname1')
        tree.add('dirname1')
        filename = pathjoin('dirname1', 'name1')
        file(filename, 'wb').write('Hello')
        tree.add(filename)
        tree.commit(message="hello")
        filename2 = pathjoin('dirname1', 'name2')
        tree.rename_one(filename, filename2)
        tree.rename_one('dirname1', 'dirname2')
        transform_tree(tree, tree.branch.basis_tree())

    def test_ignore_zero_merge_inner(self):
        # Test that merge_inner's ignore zero parameter is effective
        tree_a =self.make_branch_and_tree('a')
        tree_a.commit(message="hello")
        dir_b = tree_a.bzrdir.sprout('b')
        tree_b = dir_b.open_workingtree()
        tree_a.commit(message="hello again")
        log = StringIO()
        merge_inner(tree_b.branch, tree_a, tree_b.basis_tree(), 
                    this_tree=tree_b, ignore_zero=True)
        log = self._get_log(keep_log_file=True)
        self.failUnless('All changes applied successfully.\n' not in log)
        tree_b.revert([])
        merge_inner(tree_b.branch, tree_a, tree_b.basis_tree(), 
                    this_tree=tree_b, ignore_zero=False)
        log = self._get_log(keep_log_file=True)
        self.failUnless('All changes applied successfully.\n' in log)

    def test_merge_inner_conflicts(self):
        tree_a = self.make_branch_and_tree('a')
        tree_a.set_conflicts(ConflictList([TextConflict('patha')]))
        merge_inner(tree_a.branch, tree_a, tree_a, this_tree=tree_a)
        self.assertEqual(1, len(tree_a.conflicts()))

    def test_rmdir_conflict(self):
        tree_a = self.make_branch_and_tree('a')
        self.build_tree(['a/b/'])
        tree_a.add('b', 'b-id')
        tree_a.commit('added b')
        base_tree = tree_a.basis_tree()
        tree_z = tree_a.bzrdir.sprout('z').open_workingtree()
        self.build_tree(['a/b/c'])
        tree_a.add('b/c')
        tree_a.commit('added c')
        os.rmdir('z/b')
        tree_z.commit('removed b')
        merge_inner(tree_z.branch, tree_a, base_tree, this_tree=tree_z)
        self.assertEqual([
            conflicts.MissingParent('Created directory', 'b', 'b-id'),
            conflicts.UnversionedParent('Versioned directory', 'b', 'b-id')],
            tree_z.conflicts())
        merge_inner(tree_a.branch, tree_z.basis_tree(), base_tree, 
                    this_tree=tree_a)
        self.assertEqual([
            conflicts.DeletingParent('Not deleting', 'b', 'b-id'),
            conflicts.UnversionedParent('Versioned directory', 'b', 'b-id')],
            tree_a.conflicts())
