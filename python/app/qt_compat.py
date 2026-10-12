# MIT License

# Copyright (c) 2026 Netherlands Film Academy

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Qt compatibility layer for the delivery tool.

Newer ShotGrid / Flow Production Tracking Desktop releases run on PySide6 (Qt6).
In that case tk-core only populates ``sgtk.platform.qt6`` and leaves
``sgtk.platform.qt5`` empty. Older Desktop releases run on PySide2 (Qt5) and
only populate ``sgtk.platform.qt5``. We try Qt6 first and fall back to Qt5.

In Qt6, ``QSvgWidget`` moved from ``QtSvg`` to ``QtSvgWidgets``. ``QSvgWidget``
is exported from here so the rest of the app doesn't have to care.
"""

try:
    from sgtk.platform.qt6 import QtCore, QtSvgWidgets, QtWidgets

    QSvgWidget = QtSvgWidgets.QSvgWidget
except ImportError:
    from sgtk.platform.qt5 import QtCore, QtSvg, QtWidgets

    QSvgWidget = QtSvg.QSvgWidget

__all__ = ["QtCore", "QtWidgets", "QSvgWidget"]
