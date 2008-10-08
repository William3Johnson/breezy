# Copyright (C) 2008 Canonical Ltd
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
#

"""Tests of the 'bzr dump-btree' command."""

from bzrlib import (
    btree_index,
    tests,
    )
from bzrlib.tests import (
    http_server,
    )


class TestDumpBtree(tests.TestCaseWithTransport):

    def create_sample_btree_index(self):
        builder = btree_index.BTreeBuilder(
            reference_lists=1, key_elements=2)
        builder.add_node(('test', 'key1'), 'value', ((('ref', 'entry'),),))
        builder.add_node(('test', 'key2'), 'value2', ((('ref', 'entry2'),),))
        builder.add_node(('test2', 'key3'), 'value3', ((('ref', 'entry3'),),))
        out_f = builder.finish()
        try:
            self.build_tree_contents([('test.btree', out_f.read())])
        finally:
            out_f.close()

    def test_dump_btree_smoke(self):
        self.create_sample_btree_index()
        out, err = self.run_bzr('dump-btree test.btree')
        self.assertEqualDiff(
            "(('test', 'key1'), 'value', ((('ref', 'entry'),),))\n"
            "(('test', 'key2'), 'value2', ((('ref', 'entry2'),),))\n"
            "(('test2', 'key3'), 'value3', ((('ref', 'entry3'),),))\n",
            out)

    def test_dump_btree_http_smoke(self):
        self.transport_readonly_server = http_server.HttpServer
        self.create_sample_btree_index()
        url = self.get_readonly_url('test.btree')
        out, err = self.run_bzr(['dump-btree', url])
        self.assertEqualDiff(
            "(('test', 'key1'), 'value', ((('ref', 'entry'),),))\n"
            "(('test', 'key2'), 'value2', ((('ref', 'entry2'),),))\n"
            "(('test2', 'key3'), 'value3', ((('ref', 'entry3'),),))\n",
            out)
