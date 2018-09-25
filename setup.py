# coding=utf-8

from setuptools import setup
from setuptools.command.test import test


class TestHook(test):
    def run_tests(self):
        import nose
        nose.main(argv=['nosetests', 'tests/', '-v', '--logging-clear-handlers'])


with open('README.md') as fh:
    long_description = fh.read()

setup(
    name='tornado-httpclient-mock',
    version='0.2.3',
    description='A library for mocking requests in Tornado HTTP client',
    url='https://github.com/SuminAndrew/tornado-httpclient-mock',
    author='Andrew Sumin',
    author_email='sumin.andrew@gmail.com',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Testing',
    ],
    license='http://www.apache.org/licenses/LICENSE-2.0',
    long_description=long_description,
    long_description_content_type='text/markdown',
    cmdclass={
        'test': TestHook
    },
    packages=[
        'tornado_mock'
    ],
    install_requires=[
        'tornado',
    ],
    test_suite='tests',
    tests_require=[
        'pycodestyle',
        'pycurl'
    ],
    zip_safe=False
)
