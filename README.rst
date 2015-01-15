Python port of log2rotate
=========================

This is a rewrite of the log2rotate tool by Chris Forno. It provides the same
command line interface as the original and adds:

- keeping an arbitrary number of recent backups before applying the
  exponential rotation algorithm (--skip)

- support for arbitrary date formats (--format)

- a better detection of situations where applying the rotation algorithm
  might be dangerous (--unsafe)

- a Python module providing a Log2Rotate class that can be used to apply the
  exponential rotation algorithm to arbitrary Python objects for which
  subtraction and comparison operators can be defined.

See http://jekor.com/log2rotate


License
-------

Copyright (C) 2015 Tomaz Solc <tomaz.solc@tablix.org>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <http://www.gnu.org/licenses/>.

..
    vim: tw=75 ts=4 sw=4 expandtab softtabstop=4
