#!/usr/bin/env python

from distutils.core import setup
setup(name='gCodeU',
      version='1.0',
      author='Grega Repovs',
      description='',
      author_email='',
      url='https://bitbucket.org/mblab/gCodeU',
      package_dir={'gCodeU': '../'},
      packages=['gCodeU'],
      py_modules=['g_dicom', 'g_gimg', 'g_img', 'g_NIfTI',
                  'g_core', 'g_fidl', 'g_HCP', 'g_nipype'],
      scripts=['gmri'],
      )
