#!/usr/bin/python

from setuptools import setup

setup(name='pylog2rotate',
	version='1.0.0',
	description='Rotate backups using exponentially-growing periods.',
	license='GPL',
	long_description=open("README.rst").read(),
	author='Tomaz Solc',
	author_email='tomaz.solc@tablix.org',
	py_modules = [ 'log2rotate' ],
	entry_points = {
		'console_scripts': [
			'log2rotate = log2rotate:main'
		]
	},
	test_suite = 'tests',
)
