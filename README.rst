pylog2rotate
============

Pylog2rotate is an implementation of a backup rotation algorithm that
attempts to keep an optimal balance between data retention and space usage.

Instead of rotating backups using calendar-based periods like days, weeks
and months, it rotates backups using exponentially-growing periods. The
rotation periods are based on the base 2 logarithm. log2rotate algorithm
makes the guarantee that the distance between the nth and (n+1)th backups
will be no greater than twice the distance between the (n-1)th and nth
backups. It assumes that backups are generated at some constant period
(e.g. daily).

For a more detailed description of the algorithm, see
http://jekor.com/log2rotate

This package provides a Python library that implements the log2rotate
algorithm and a command-line tool.

Usage from command line
-----------------------

The ``log2rotate`` tool takes a list of backup names on the standard input
and writes a list of backup names on the standard output. It can return a
list of names to delete (``--delete`` option) or a list of names to keep
(``--keep`` option).

The command-line tool at the moment assumes that backups are generated
daily and that backup names contain the date of the backup. Exact
formatting of the names can be specified using the ``--format`` option and
the `strptime syntax <https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior>`_.

The ``--skip`` option allows you to keep a certain period of backups before
applying the rotation algorithm. If some backups are missing in the series
(for example, if a machine was off-line for a day), you can specify a fuzzy
matching factor with the ``--fuzz`` option. Without it, ``log2rotate`` will
exit with an error if it sees any deviation from the expected pattern of
backups.

For example, if a daily cronjob is creating backups::

    tarsnap -cf backup-`date +%Y%m%d` .

Then backups can be rotated using a script like this::

    for name in `tarsnap --list-archives | log2rotate --delete --format "backup-%Y%m%d"`; do
        tarsnap -df $name
    done

The backup rotation script can be run after each backup, or less
frequently. The rotation algorithm is idempotent.

See ``log2rotate --help`` for a full list of available options.

Python library
--------------

The Python library can be used to apply the exponential rotation algorithm
to arbitrary Python objects for which a subtraction operator can be
defined.

The ``Log2Rotate`` class implements the rotation algorithm. Backup state is
kept as a list of backup objects. You call the ``backups_to_keep()`` method
with the old state to get a new state::

    >>> from log2rotate import Log2Rotate
    >>> l2r = Log2Rotate()
    >>> state = [1, 2, 3, 4]
    >>> l2r.backups_to_keep(state)
    [1, 3, 4]

To apply the algorithm to arbitrary Python objects, subclass ``Log2Rotate``
and override the ``sub()`` method. The ``sub()`` method takes two backup
objects and returns the number of backup periods between them.

For instance, if you keep backup creation time as a ``datetime`` object in
a ``created`` property, and backups are created daily, you could implement
``sub()`` like this::

    def sub(self, x, y):
        return (x.created - y.created).days

For details, see library source.

History
-------

Pylog2rotate is a rewrite of the ``log2rotate`` tool by Chris Forno. It
provides the same command line interface as the original and adds:

- keeping an arbitrary number of recent backups before applying the
  exponential rotation algorithm (``--skip``)

- limited fuzzy matching in case of missing backups (``--fuzz``)

- support for arbitrary date formats (``--format``)

- a better detection of situations where applying the rotation algorithm
  might be dangerous (``--unsafe``)

- a Python module providing a ``Log2Rotate`` class.

See http://jekor.com/log2rotate

Fuzzy matching produces better results than ``--unsafe`` in case occasional
backups are missing from the series. With fuzzy matching, an older backup
is selected for long-term keeping if the exact backup selected by the
log2rotate algorithm is missing.

License
-------

Copyright (C) 2016 Tomaz Solc <tomaz.solc@tablix.org>

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

See Also
--------

 * grandfatherson  implements the alternate Grandfather Father Son rotation algorithm in Python. https://github.com/ecometrica/grandfatherson

..
    vim: tw=75 ts=4 sw=4 expandtab softtabstop=4
