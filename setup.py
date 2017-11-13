import versioneer # https://github.com/warner/python-versioneer
from distutils.core import setup

setup(name="pyvdrive",
      version=versioneer.get_version(), #"0.2.2",
      cmdclass=versioneer.get_cmdclass(),
      description = "Vulcan Data Reduction and Analysis",
      author = "Wenduo Zhou",
      author_email = "zhouw@ornl.gov",
      url = "https://github.com/neutrons/PyVDrive",
      long_description = """Vulcan data reduction and analysis""",
      license = "The MIT License (MIT)",
      scripts=["scripts/Lava.py"],
      packages=["pyvdrive", "pyvdrive/lib", "pyvdrive/interface", "pyvdrive/interface/gui", "pyvdrive/interface/gui/ndav_widgets", "pyvdrive/interface/vdrive_commands/"],
      package_dir={},#'finddata': '.'},
      #data_files=[('/etc/bash_completion.d/', ['finddata.bashcomplete'])]
)
