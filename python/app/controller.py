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

"""Controller for delivery tool, written by Mervin van Brakel 2024.

Reworked: shows all shots grouped per sequence with checkboxes and delivers
only the checked shots, without depending on the shot status.
"""

import sgtk

from .qt_compat import QtCore, QtWidgets
from . import model, view

logger = sgtk.platform.get_logger(__name__)


def open_delivery_app(app_instance):
    """Opens up the app. Is called when user clicks on the delivery button."""
    app_instance.engine.show_dialog("Deliveries", app_instance, DeliveryController)


class DeliveryController(QtWidgets.QWidget):
    """The controller for the delivery application."""

    def __init__(self):
        self.view = view.DeliveryView()
        self.view.create_user_interface(self)
        self.model = model.DeliveryModel(sgtk.platform.current_bundle(), logger)
        self.shots_by_id = {}
        self.load_thread = None
        self.export_thread = None
        self.connect_signals()
        self.load_shots()
        QtCore.QTimer.singleShot(0, self.bring_to_front)

    def bring_to_front(self):
        """Raises the dialog above other applications when it opens.

        The app runs in a separate process from the Desktop window, so Windows
        doesn't give it focus by itself. Briefly setting 'stay on top' forces
        the window to the front; it's removed again right after.
        """
        window = self.window()
        flags = window.windowFlags()
        window.setWindowFlags(flags | QtCore.Qt.WindowStaysOnTopHint)
        window.show()
        window.raise_()
        window.activateWindow()
        window.setWindowFlags(flags)
        window.show()
        window.raise_()
        window.activateWindow()

    def connect_signals(self):
        v = self.view
        v.reload_button.clicked.connect(self.load_shots)
        v.export_shots_button.clicked.connect(self.export_shots)
        v.open_delivery_folder_button.clicked.connect(self.model.open_delivery_folder)
        v.select_all_button.clicked.connect(lambda: v.set_all_checked(True))
        v.select_none_button.clicked.connect(lambda: v.set_all_checked(False))
        v.expand_button.clicked.connect(v.tree.expandAll)
        v.collapse_button.clicked.connect(v.tree.collapseAll)
        v.filter_field.textChanged.connect(v.apply_filter)
        v.tree.itemChanged.connect(lambda *_: self.update_selection_label())

    # --------------------------------------------------------------- loading
    def load_shots(self):
        if self.export_thread and self.export_thread.isRunning():
            return
        self.view.clear_shots()
        self.view.status_label.setText("")
        self.view.loading_widget.show()
        self.view.set_busy(True)

        self.load_thread = model.LoadShotsThread(self.model)
        self.load_thread.loading_shots_successful.connect(self.loading_shots_successful)
        self.load_thread.loading_shots_failed.connect(self.loading_shots_failed)
        self.load_thread.start()

    def loading_shots_successful(self, shots):
        self.view.loading_widget.hide()
        self.view.set_busy(False)
        # Only list shots that can actually be delivered (have a published file).
        shots = [shot for shot in shots if not shot["load_error"]]
        self.shots_by_id = {shot["id"]: shot for shot in shots}
        self.view.populate_shots(shots)
        self.view.apply_filter(self.view.filter_field.text())
        self.update_selection_label()

    def loading_shots_failed(self, error: str):
        logger.error(f"Error while loading shots: {error}")
        self.view.loading_widget.hide()
        self.view.set_busy(False)
        self.view.status_label.setText(f"Error while loading shots: {error}")

    def update_selection_label(self):
        if self.export_thread and self.export_thread.isRunning():
            return
        count = len(self.view.checked_shot_ids())
        total = len(self.shots_by_id)
        self.view.status_label.setText(f"{count} of {total} shots selected")

    # -------------------------------------------------------------- delivery
    def export_shots(self):
        shot_ids = self.view.checked_shot_ids()
        if not shot_ids:
            QtWidgets.QMessageBox.information(
                self, "Deliveries", "No shots selected. Tick the shots you want to deliver."
            )
            return

        answer = QtWidgets.QMessageBox.question(
            self,
            "Deliveries",
            f"Deliver the latest version of {len(shot_ids)} shot(s)?",
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return

        # Keep tree order (sequence / shot).
        shots = [self.shots_by_id[i] for i in self.shots_by_id if i in set(shot_ids)]

        self.view.reset_results(shot_ids)
        self.view.set_busy(True)
        self.view.status_label.setText(f"Delivering {len(shots)} shot(s)...")

        self.export_thread = model.ExportShotsThread(self.model, shots)
        self.export_thread.shot_message.connect(
            lambda shot_id, msg: self.view.set_shot_message(shot_id, msg)
        )
        self.export_thread.shot_error.connect(
            lambda shot_id, msg: self.view.set_shot_message(shot_id, msg, error=True)
        )
        self.export_thread.shot_progress.connect(self.view.set_shot_progress)
        self.export_thread.export_finished.connect(self.export_finished)
        self.export_thread.start()

    def export_finished(self, delivered: int, failed: int):
        self.view.set_busy(False)
        text = f"Delivered {delivered} shot(s)."
        if failed:
            text += f" {failed} shot(s) failed, see the Result column."
        self.view.status_label.setText(text)
