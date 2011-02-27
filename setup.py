#!/bin/env python

from distutils.core import setup

from haikuports import __version__


setup(
    name='haikuports',
    version=__version__,
    packages=['haikuports'],
    scripts=['hpbuild'],

    author="HaikuPorts team",
    author_email="brecht@mos6581.org",
    description="Python package for building Haiku ports",
    license="GPL",
    keywords="HaikuPorts",
    url="http://ports.haiku-files.org",
)
