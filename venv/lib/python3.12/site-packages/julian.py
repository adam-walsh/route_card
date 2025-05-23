#!/usr/bin/env python3
# https://www.wayforward.net/magvar/julian.py
#
# Copyright(c) 2024, Wayforward Technology, LLC
#
# Author: Terence Way <terry@wayforward.net>
#
"""Convert Python date and datetime objects into a floating-point Julian
time, suitable for passing into the magvar.magnetic_variation function.
"""

from datetime import datetime

def is_leap(year):
    """True iff _year_ is a leap year:

    >>> is_leap(1992)
    True

    >>> is_leap(1993)
    False

    >>> is_leap(1999)
    False

    >>> is_leap(2000)
    True

    >>> is_leap(2100)
    False
    """
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def days_in_year(year):
    """Returns 366 iff year is a leap year.  Returns 365 otherwise.

    >>> days_in_year(2000)
    366

    >>> days_in_year(2100)
    365

    >>> days_in_year(2021)
    365

    >>> days_in_year(2024)
    366
    """
    return [365, 366][int(is_leap(year))]

def julian(dt):
    """
    Returns floating point "julian" date.

    >>> julian(datetime(2022, 1, 1))
    2022.0

    >>> round(julian(datetime(2022, 1, 2)), 4)
    2022.0027

    >>> round(julian(datetime(2022, 12, 31)), 4)
    2022.9973
    """
    if hasattr(dt, 'timetuple'):
        t = dt.timetuple()
        y = t.tm_year
        return y + (t.tm_yday - 1) / days_in_year(y)

    return float(dt)

def _test():
    from doctest import testmod
    return testmod()

if __name__ == '__main__':
    _test() 
