from distutils.core import setup

setup(
    name='botomfa',
    version='0.2',
    author='Brian Nuszkowski',
    py_modules=['botomfa'],
    install_requires=['boto'],
    data_files=[('/usr/bin', ['botomfa'])]
)
