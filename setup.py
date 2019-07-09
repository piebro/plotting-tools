"""
Based on https://github.com/pypa/sampleproject

"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

#here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
#with open(path.join(here, 'README.txt'), encoding='utf-8') as f:
#    long_description = f.read()

setup(
    name='py_plotting_tools',
    version='0.0.1',
    long_description='long_description',
    long_description_content_type='text/plain',
    url='',
    author='',
    author_email='',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        'pyaxidraw'
    ],
    entry_points={
        'console_scripts': [
            'pre_process = plotting_tools:pre_process_main',
            'plot=plotting_tools:plot',
            'pre_process_config = plotting_tools:edit_pre_process_config',
            'plot_config = plotting_tools:edit_axidraw_config'
        ]
    }
)