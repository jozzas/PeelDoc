PeelDoc
=======

PeelDoc is a detailed documentation generator for SQL and PL/SQL code, similar to Doxygen. 
Adapted from HyperSQL v1.0 by Randy Phillips.

License
-------
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

About
-----
PeelDoc generates detailed documentation (similar to Doxygen) for PL/SQL and SQL files.
It extracts the code structure from these files and generates a set of HTML files which can be navigated.

PeelDoc runs in any environment capable of running python 2.X and uses only standard libraries. No installation
is required, as long as you have a working python interpreter.

Usage
-----

`python PeelDoc.py path_to_files`

Generated output is placed in `(directory where PeelDoc resides)/html/`


Version History
---------------

*v0.1 (Beta)*

Initial version, adapted from HyperSQL v1.0 by Randy Phillips. Extensions on
HyperSQL include:

- W3C valid html output
- use of customisable CSS
- Cleaned up file parsing
- Now ignores .svn, .cvs subdirectories
- searches across .sql, .bdy, .qf and .pls files
