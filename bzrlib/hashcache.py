# (C) 2005 Canonical Ltd

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA




def _fingerprint(abspath):
    import os, stat

    try:
        fs = os.lstat(abspath)
    except OSError:
        # might be missing, etc
        return None

    if stat.S_ISDIR(fs.st_mode):
        return None

    return (fs.st_size, fs.st_mtime,
            fs.st_ctime, fs.st_ino, fs.st_dev)


class HashCache(object):
    """Cache for looking up file SHA-1.

    Files are considered to match the cached value if the fingerprint
    of the file has not changed.  This includes its mtime, ctime,
    device number, inode number, and size.  This should catch
    modifications or replacement of the file by a new one.

    This may not catch modifications that do not change the file's
    size and that occur within the resolution window of the
    timestamps.  To handle this we specifically do not cache files
    which have changed since the start of the present second, since
    they could undetectably change again.

    This scheme may fail if the machine's clock steps backwards.
    Don't do that.

    This does not canonicalize the paths passed in; that should be
    done by the caller.

    cache_sha1
        Indexed by path, gives the SHA-1 of the file.

    validator
        Indexed by path, gives the fingerprint of the file last time it was read.

    stat_count
        number of times files have been statted

    hit_count
        number of times files have been retrieved from the cache, avoiding a
        re-read
        
    miss_count
        number of misses (times files have been completely re-read)
    """
    def __init__(self, basedir):
        self.basedir = basedir
        self.hit_count = 0
        self.miss_count = 0
        self.stat_count = 0
        self.danger_count = 0
        self.cache_sha1 = {}
        self.validator = {}


    def clear(self):
        """Discard all cached information."""
        self.validator = {}
        self.cache_sha1 = {}


    def get_sha1(self, path):
        """Return the hex SHA-1 of the contents of the file at path.

        XXX: If the file does not exist or is not a plain file???
        """

        import os, time
        from bzrlib.osutils import sha_file
        
        abspath = os.path.join(self.basedir, path)
        fp = _fingerprint(abspath)
        cache_fp = self.validator.get(path)

        self.stat_count += 1

        if not fp:
            # not a regular file
            return None
        elif cache_fp and (cache_fp == fp):
            self.hit_count += 1
            return self.cache_sha1[path]
        else:
            self.miss_count += 1
            digest = sha_file(file(abspath, 'rb'))

            now = int(time.time())
            if fp[1] >= now or fp[2] >= now:
                # changed too recently; can't be cached.  we can
                # return the result and it could possibly be cached
                # next time.
                self.danger_count += 1 
                if cache_fp:
                    del self.validator[path]
                    del self.cache_sha1[path]
            else:
                self.validator[path] = fp
                self.cache_sha1[path] = digest

            return digest

