from distutils.core import setup

setup(name="stellar-magnate",
        version="0.1",
        description="A space-themed commodity trading game",
        long_description="""
Stellar Magnate is a space-themed trading game in the spirit of Planetary
Travel, a trading game for the Apple IIe by Brian Winn.
        """,
        author="Toshio Kuratomi",
        author_email="toshio@fedoraproject.org",
        maintainer="Toshio Kuratomi",
        maintainer_email="toshio@fedoraproject.org",
        url="https://github.com/abadger/pubmarine",
        license="GNU Affero General Public License v3+",
        keywords='game trading',
        classifiers=[
            'Development Status :: 3 - Alpha',
            #'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            #'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        packages=['magnate', 'magnate.ui'],
        scripts=['bin/magnate'],
        install_requires=['pubmarine >= 0.3', 'urwid'],
    )
