"""Tests for distutils.command.bdist_dumb."""

import unittest2
import sys
import os

# zlib is not used here, but if it's not available
# test_simple_built will fail
try:
    import zlib
except ImportError:
    zlib = None

from test.test_support import run_unittest

from distutils2.core import Distribution
from distutils2.command.bdist_dumb import bdist_dumb
from distutils2.tests import support

SETUP_PY = """\
from distutils.core import setup
import foo

setup(name='foo', version='0.1', py_modules=['foo'],
      url='xxx', author='xxx', author_email='xxx')

"""

class BuildDumbTestCase(support.TempdirManager,
                        support.LoggingSilencer,
                        support.EnvironGuard,
                        unittest2.TestCase):

    def setUp(self):
        super(BuildDumbTestCase, self).setUp()
        self.old_location = os.getcwd()
        self.old_sys_argv = sys.argv, sys.argv[:]

    def tearDown(self):
        os.chdir(self.old_location)
        sys.argv = self.old_sys_argv[0]
        sys.argv[:] = self.old_sys_argv[1]
        super(BuildDumbTestCase, self).tearDown()

    @unittest2.skipUnless(zlib, "requires zlib")
    def test_simple_built(self):

        # let's create a simple package
        tmp_dir = self.mkdtemp()
        pkg_dir = os.path.join(tmp_dir, 'foo')
        os.mkdir(pkg_dir)
        self.write_file((pkg_dir, 'setup.py'), SETUP_PY)
        self.write_file((pkg_dir, 'foo.py'), '#')
        self.write_file((pkg_dir, 'MANIFEST.in'), 'include foo.py')
        self.write_file((pkg_dir, 'README'), '')

        dist = Distribution({'name': 'foo', 'version': '0.1',
                             'py_modules': ['foo'],
                             'url': 'xxx', 'author': 'xxx',
                             'author_email': 'xxx'})
        dist.script_name = 'setup.py'
        os.chdir(pkg_dir)

        sys.argv = ['setup.py']
        cmd = bdist_dumb(dist)

        # so the output is the same no matter
        # what is the platform
        cmd.format = 'zip'

        cmd.ensure_finalized()
        cmd.run()

        # see what we have
        dist_created = os.listdir(os.path.join(pkg_dir, 'dist'))
        base = "%s.%s" % (dist.get_fullname(), cmd.plat_name)
        if os.name == 'os2':
            base = base.replace(':', '-')

        wanted = ['%s.zip' % base]
        self.assertEquals(dist_created, wanted)

        # now let's check what we have in the zip file
        # XXX to be done

    def test_finalize_options(self):
        pkg_dir, dist = self.create_dist()
        os.chdir(pkg_dir)
        cmd = bdist_dumb(dist)
        self.assertEquals(cmd.bdist_dir, None)
        cmd.finalize_options()

        # bdist_dir is initialized to bdist_base/dumb if not set
        base = cmd.get_finalized_command('bdist').bdist_base
        self.assertEquals(cmd.bdist_dir, os.path.join(base, 'dumb'))

        # the format is set to a default value depending on the os.name
        default = cmd.default_format[os.name]
        self.assertEquals(cmd.format, default)

def test_suite():
    return unittest2.makeSuite(BuildDumbTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
