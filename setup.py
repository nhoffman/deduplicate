"""
install package:        python setup.py install
create unix package:    python setup.py sdist
"""

from distutils.core import setup
import glob

from deduplicate.__init__ import __version__

# all files with .py extension in top level are assumed to be scripts
scripts = list(set(glob.glob('*.py')) - set(['setup.py']))

params = {'author': 'Noah Hoffman',
          'author_email': 'noah.hoffman@gmail.com',
          'description': 'Remove duplicates from collections of biological sequences',
          'name': 'deduplicate',
          'package_dir': {'deduplicate': 'deduplicate'},
          'packages': ['deduplicate'],
          'scripts': scripts,
          'url': 'http://github.com/nhoffman/deduplicate',
          'version': __version__,
          'requires':['python (>= 2.7)']}

setup(**params)
