# MIT License

# Copyright (c) 2024 Netherlands Film Academy

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

"""View for delivery tool, written by Mervin van Brakel 2024.

Reworked: tree of all shots grouped per sequence, with checkboxes.
"""

from pathlib import Path

from .qt_compat import QSvgWidget, QtCore, QtGui, QtWidgets

SCRIPT_LOCATION: Path = Path(__file__).parent

COLOR_OK = "#8BFF3E"
COLOR_ERROR = "#FF3E3E"
COLOR_MUTED = "#888888"

COL_SHOT, COL_STATUS, COL_VERSION, COL_FRAMES, COL_PROGRESS, COL_RESULT = range(6)


class DeliveryView:
    """All Qt UI for the ShotGrid delivery application."""

    def __init__(self) -> None:
        # shot id -> {"item": QTreeWidgetItem, "progress": QProgressBar}
        self.shot_items = {}
        self.sequence_items = []

    def create_user_interface(self, main_widget: QtWidgets.QWidget):
        QtWidgets.QWidget.__init__(main_widget)
        main_widget.resize(900, 650)

        self.layout = QtWidgets.QVBoxLayout(main_widget)
        self.layout.addWidget(self.get_explanation_widget())
        self.layout.addWidget(self.get_toolbar_widget())
        self.layout.addWidget(self.get_tree_widget(), 1)
        self.layout.addWidget(self.get_loading_widget())
        self.layout.addWidget(self.get_buttons_widget())

    @staticmethod
    def get_explanation_widget() -> QtWidgets.QWidget:
        label = QtWidgets.QLabel(
            "Select the shots you want to deliver. The latest version of each "
            "selected shot is delivered to the delivery folder with the correct "
            "naming convention. Shot statuses are not changed."
        )
        label.setWordWrap(True)
        return label

    def get_toolbar_widget(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.filter_field = QtWidgets.QLineEdit()
        self.filter_field.setPlaceholderText("Filter sequence or shot...")
        self.filter_field.setClearButtonEnabled(True)
        layout.addWidget(self.filter_field, 1)

        self.select_all_button = QtWidgets.QPushButton("Select all")
        self.select_none_button = QtWidgets.QPushButton("Select none")
        self.expand_button = QtWidgets.QPushButton("Expand all")
        self.collapse_button = QtWidgets.QPushButton("Collapse all")
        for button in (
            self.select_all_button,
            self.select_none_button,
            self.expand_button,
            self.collapse_button,
        ):
            layout.addWidget(button)
        return widget

    def get_tree_widget(self) -> QtWidgets.QTreeWidget:
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(
            ["Shot", "Status", "Version", "Frames", "Progress", "Result"]
        )
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        header = self.tree.header()
        header.setStretchLastSection(True)
        self.tree.setColumnWidth(COL_SHOT, 200)
        self.tree.setColumnWidth(COL_STATUS, 70)
        self.tree.setColumnWidth(COL_VERSION, 70)
        self.tree.setColumnWidth(COL_FRAMES, 100)
        self.tree.setColumnWidth(COL_PROGRESS, 150)
        return self.tree

    def get_loading_widget(self) -> QtWidgets.QWidget:
        self.loading_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.loading_widget)
        spinner = QSvgWidget(
            str(SCRIPT_LOCATION / "../.." / "resources" / "loading_spinner.svg")
        )
        spinner.setFixedSize(60, 60)
        layout.addWidget(spinner, 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(QtWidgets.QLabel("Loading shots..."), 0, QtCore.Qt.AlignHCenter)
        self.loading_widget.hide()
        return self.loading_widget

    def get_buttons_widget(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label, 1)

        self.reload_button = QtWidgets.QPushButton("Reload")
        self.open_delivery_folder_button = QtWidgets.QPushButton("Open delivery folder")
        self.export_shots_button = QtWidgets.QPushButton("Deliver selected")
        self.export_shots_button.setDefault(True)
        for button in (
            self.reload_button,
            self.open_delivery_folder_button,
            self.export_shots_button,
        ):
            layout.addWidget(button)
        return widget

    # ------------------------------------------------------------- populate
    def clear_shots(self) -> None:
        self.tree.clear()
        self.shot_items = {}
        self.sequence_items = []

    def populate_shots(self, shots: list[dict]) -> None:
        """Fills the tree. Shots must already be sorted by sequence."""
        self.tree.blockSignals(True)
        self.clear_shots()

        sequence_item = None
        for shot in shots:
            if sequence_item is None or sequence_item.text(COL_SHOT) != shot["sequence"]:
                sequence_item = QtWidgets.QTreeWidgetItem(self.tree, [shot["sequence"]])
                sequence_item.setFlags(
                    sequence_item.flags()
                    | QtCore.Qt.ItemIsUserCheckable
                    | QtCore.Qt.ItemIsAutoTristate
                )
                sequence_item.setCheckState(COL_SHOT, QtCore.Qt.Unchecked)
                font = sequence_item.font(COL_SHOT)
                font.setBold(True)
                sequence_item.setFont(COL_SHOT, font)
                self.sequence_items.append(sequence_item)

            self.add_shot_item(sequence_item, shot)

        for item in self.sequence_items:
            item.setExpanded(True)
        self.tree.blockSignals(False)

    def add_shot_item(self, parent: QtWidgets.QTreeWidgetItem, shot: dict) -> None:
        frames = (
            f"{shot['first_frame']} - {shot['last_frame']}"
            if shot["first_frame"] is not None and shot["last_frame"] is not None
            else "-"
        )
        version = f"v{shot['version_number']:03d}" if shot["version_number"] else "-"
        item = QtWidgets.QTreeWidgetItem(
            parent, [shot["shot"], shot["status"] or "", version, frames, "", ""]
        )
        item.setData(COL_SHOT, QtCore.Qt.UserRole, shot["id"])

        if shot["load_error"]:
            # Not deliverable: show why, and don't allow checking it.
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsUserCheckable)
            item.setText(COL_RESULT, shot["load_error"])
            for column in range(6):
                item.setForeground(column, _brush(COLOR_MUTED))
        else:
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(
                COL_SHOT,
                QtCore.Qt.Checked if shot["preselected"] else QtCore.Qt.Unchecked,
            )
            if shot["version_name"]:
                item.setToolTip(COL_VERSION, shot["version_name"])

        progress = QtWidgets.QProgressBar()
        progress.setMaximumHeight(14)
        progress.setTextVisible(False)
        progress.setStyleSheet(
            f"QProgressBar::chunk {{background-color: {COLOR_OK};}} "
            "QProgressBar {background-color: #444444; border: none;}"
        )
        if shot["first_frame"] is not None and shot["last_frame"] is not None:
            progress.setRange(shot["first_frame"], shot["last_frame"])
            progress.setValue(shot["first_frame"])
        progress.hide()
        self.tree.setItemWidget(item, COL_PROGRESS, progress)

        self.shot_items[shot["id"]] = {"item": item, "progress": progress}

    # ---------------------------------------------------------------- state
    def checked_shot_ids(self) -> list[int]:
        return [
            shot_id
            for shot_id, refs in self.shot_items.items()
            if refs["item"].flags() & QtCore.Qt.ItemIsUserCheckable
            and refs["item"].checkState(COL_SHOT) == QtCore.Qt.Checked
        ]

    def set_all_checked(self, checked: bool) -> None:
        """Checks/unchecks all visible deliverable shots."""
        state = QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked
        for refs in self.shot_items.values():
            item = refs["item"]
            if not item.isHidden() and item.flags() & QtCore.Qt.ItemIsUserCheckable:
                item.setCheckState(COL_SHOT, state)

    def apply_filter(self, text: str) -> None:
        text = text.strip().lower()
        for sequence_item in self.sequence_items:
            sequence_match = text in sequence_item.text(COL_SHOT).lower()
            any_visible = False
            for index in range(sequence_item.childCount()):
                child = sequence_item.child(index)
                visible = not text or sequence_match or text in child.text(COL_SHOT).lower()
                child.setHidden(not visible)
                any_visible = any_visible or visible
            sequence_item.setHidden(not any_visible)

    def set_shot_message(self, shot_id: int, message: str, error: bool = False) -> None:
        refs = self.shot_items.get(shot_id)
        if not refs:
            return
        refs["item"].setText(COL_RESULT, message)
        refs["item"].setToolTip(COL_RESULT, message)
        refs["item"].setForeground(COL_RESULT, _brush(COLOR_ERROR if error else COLOR_OK))
        if error:
            refs["progress"].hide()

    def set_shot_progress(self, shot_id: int, frame: int) -> None:
        refs = self.shot_items.get(shot_id)
        if refs:
            refs["progress"].show()
            refs["progress"].setValue(frame)

    def reset_results(self, shot_ids: list[int]) -> None:
        for shot_id in shot_ids:
            refs = self.shot_items[shot_id]
            refs["item"].setText(COL_RESULT, "Waiting...")
            refs["item"].setForeground(COL_RESULT, _brush(COLOR_MUTED))
            refs["progress"].setValue(refs["progress"].minimum())
            refs["progress"].hide()

    def set_busy(self, busy: bool) -> None:
        for widget in (
            self.export_shots_button,
            self.reload_button,
            self.select_all_button,
            self.select_none_button,
        ):
            widget.setEnabled(not busy)


def _brush(color: str):
    return QtGui.QBrush(QtGui.QColor(color))
