File2Package.py [![Unlicensed work](https://raw.githubusercontent.com/unlicense/unlicense.org/master/static/favicon.png)](https://unlicense.org/)
=========
[![GitLab Build Status](https://gitlab.com/KOLANICH/File2Package.py/badges/master/pipeline.svg)](https://gitlab.com/KOLANICH/File2Package.py/pipelines/master/latest)
![GitLab Coverage](https://gitlab.com/KOLANICH/File2Package.py/badges/master/coverage.svg)
[![Coveralls Coverage](https://img.shields.io/coveralls/KOLANICH/File2Package.py.svg)](https://coveralls.io/r/KOLANICH/File2Package.py)
[![Libraries.io Status](https://img.shields.io/librariesio/github/KOLANICH/File2Package.py.svg)](https://libraries.io/github/KOLANICH/File2Package.py)

Just stores some data identifying packages in a SQLite DB and paths of their files in a prefix tree. Allows you to get a package by a file.

See [`tests/tests.py`](./tests/tests.py) for the examples.

Requirements
------------
* [`Python >=3.4`](https://www.python.org/downloads/). [`Python 2` is dead, stop raping its corpse.](https://python3statement.org/) Use `2to3` with manual postprocessing to migrate incompatible code to `3`. It shouldn't take so much time. For unit-testing you need Python 3.6+ or PyPy3 because their `dict` is ordered and deterministic. Python 3 is also semi-dead, 3.7 is the last minor release in 3.
* [`datrie`](https://github.com/pytries/datrie) for a prefix tree.
