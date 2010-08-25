import os, sys, shutil
from subprocess import check_call
from distutils2.metadata import DistributionMetadata

# This are global constants. Do not change.
is_win32 = (sys.platform == 'win32')

# This option not working (yet).  Should we use setup() from distutils2?
use_distutils2 = '--distutils2' in sys.argv

if use_distutils2:
    from distutils2 import setup
else:
    from setuptools import setup
    from distutils.command.build import build as _build
    from setuptools.command.install import install as _install

    # Configure cmake if it hasn't been done already.
    def cmake_configure(src_dir, build_dir, install_cmd):
        if not os.path.isfile(os.path.join(build_dir, 'CMakeCache.txt')):

            # create a CMake build directory in build_dir that is
            # prepared to build code in src_dir
            if not os.path.isdir(build_dir):
                os.makedirs(build_dir)

            # use the install_scripts directory as calculated by setuptools
            # Note: we'll need to let users override this on the command line
            check_call([
                    'cmake', 
                    '-DCMAKE_INSTALL_PREFIX='+install_cmd.install_scripts, 
                    os.path.abspath(src_dir)], 
                       cwd=build_dir, shell=is_win32)

    def is_cmake_project(dir):
        return os.path.isfile(os.path.join(dir, 'CMakeLists.txt'))

    # setuptools command object to execute during ryppl build
    class cmake_build(_build):
        def run (self):
            src_dir = os.getcwd()
            if is_cmake_project(src_dir):
                # Setuptools doesn't calculate the install directories
                # until 'install' is called, but we need them here in
                # 'build' so we can configure cmake.
                install_cmd = cmake_install()
                install_cmd.finalize_options()
  
                # Configure cmake if it hasn't been done already.
                cmake_configure(src_dir, self.build_base, install_cmd)
  
                # actually build 
                check_call(['cmake', '--build', self.build_base], shell=is_win32)
            else:
                _build.run(self)

    # setuptools command object to execute during ryppl install
    class cmake_install(_install):
        def run (self):
            src_dir = os.getcwd()
            if is_cmake_project(src_dir):
                # Configure cmake if it hasn't been done already.
                cmake_configure(src_dir, self.build_base, self)

                # Now install it.
                check_call(['cmake', '--build', '.', '--target', 'install'], cwd=self.build_base, shell=is_win32)

                # install the .egg-info for this guy
                self.run_command('install_egg_info')

                # Copy the install_manifest.txt to the install record file
                shutil.copy2(os.path.join(self.build_base, 'install_manifest.txt'), self.record)

                # Add the .egg-info directory and its contents to the install_record.txt
                ei = self.get_finalized_command('install_egg_info')
                open(self.record, 'a+').write( '\n'.join(ei.get_outputs())+'\n' )

            else:
                _install.run(self)

# Read the metadata out of the project's .ryppl/METADATA file
metadata = DistributionMetadata(
    path=os.path.join(os.getcwd(), '.ryppl', 'METADATA'),
    platform_dependant=True
    )

def metadata_to_setup_keywords(metadata):
    """
    Convert a Distutils2 metadata object into a dict of named
    arguments to be passed to setup()
    """
    if use_distutils2:
        # Everything *should* be this easy.
        return dict( metadata.items() )
    else:
        class item_to_attribute(object):
            """
            because I hate seeing identifiers between quotes
            """
            def __init__(self, target):
                self.target = target

            def __getattr__(self, name):
                return self.target[name]

        m = item_to_attribute(metadata)
        # There's probably a more declarative way, but until then, I just
        # copied these keywords out of the distutils source.
        # EAN: these parameters are documented at
        # http://docs.python.org/distutils/apiref.html
        return dict(
          # This hooks various ryppl commands to do our bidding.
            cmdclass = {
                'build'             : cmake_build,
                'install'           : cmake_install
                },

            name = m.name,
            version = m.version,
            author = m.author,
            author_email = m.author_email,
            maintainer = m.maintainer,
            maintainer_email = m.maintainer_email,
            url = m.project_url,
            description = m.summary,
            long_description = m.description,
            keywords = ' '.join(m.keywords),
            platforms = m.platform,
            classifiers = m.classifier, 
            download_url = m.download_url,
            install_requires = m.requires_dist or m.requires,
            provides = m.provides_dist or m.provides,
            obsoletes = m.obsoletes_dist or m.obsoletes,
          )

# Call setup with keyword arguments corresponding to the metadata
setup( **metadata_to_setup_keywords(metadata) )
