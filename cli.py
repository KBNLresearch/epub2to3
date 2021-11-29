#! /usr/bin/env python
#
"""CLI wrapper script, ensures that relative imports work correctly in a PyInstaller build"""

from epub2to3.epub2to3 import main

if __name__ == '__main__':
    main()
