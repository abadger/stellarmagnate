from distutils.core import setup

setup(name="stellar-magnate",
        version="0.1",
        description="A space-themed commodity trading game",
        long_description="""
Stellar Magnate is a space-themed trading game in the spirit of Planetary
Travel by Brian Winn.
        """,
        author="Toshio Kuratomi",
        author_email="toshio@fedoraproject.org",
        maintainer="Toshio Kuratomi",
        maintainer_email="toshio@fedoraproject.org",
        url="https://github.com/abadger/pubmarine",
        license="GNU Affero General Public License v3 or later (AGPLv3+)",
        keywords='game trading',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console :: Curses',
            'Intended Audience :: End Users/Desktop',
            'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Games/Entertainment',
            'Topic :: Games/Entertainment :: Simulation',
        ],
        packages=['magnate', 'magnate.ui'],
        scripts=['bin/magnate'],
        install_requires=['ConfigObj', 'PyYaml', 'attrs', 'jsonschema', 'kitchen', 'pubmarine >= 0.3', 'straight.plugin', 'urwid'],
    )
