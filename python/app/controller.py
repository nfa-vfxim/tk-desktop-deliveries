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

"""Controller for delivery tool, written by Mervin van Brakel 2024"""

import sgtk
from sgtk.platform.qt5 import QtWidgets

from . import model, view

logger = sgtk.platform.get_logger(__name__)


def open_delivery_app(app_instance):
    """
    Opens up the app. Is called when user clicks on the delivery button.
    """

    app_instance.engine.show_dialog(
        "Deliveries", app_instance, DeliveryController
    )


class DeliveryController(QtWidgets.QWidget):
    """
    The controller for the delivery application.
    """

    def __init__(self):
        """
        Initializes the controller.
        """
        self.view = view.DeliveryView()
        self.view.create_user_interface(self)
        self.model = model.DeliveryModel(
            sgtk.platform.current_bundle(), logger
        )
        self.connect_buttons()
        self.load_shots()

    def connect_buttons(self):
        """Connects the buttons from our view to our controller function."""
        self.view.reload_button.clicked.connect(self.load_shots)
        self.view.export_shots_button.clicked.connect(self.export_shots)
        self.view.open_delivery_folder_button.clicked.connect(
            self.open_delivery_folder
        )

    def load_shots(self):
        """Clear the olds shots, then fetches the shots on the model."""
        self.view.final_validation_label.hide()

        for shot in self.view.shot_widget_references:
            self.view.shot_widget_references[shot]["widget"].hide()
            self.view.shots_list_widget_layout.removeWidget(
                self.view.shot_widget_references[shot]["widget"]
            )

        self.view.loading_widget.show()
        self.model.load_shots(
            self.loading_shots_successful,
            self.loading_shots_failed,
        )

    def loading_shots_successful(self, shots_to_deliver):
        """Runs when shots have finished loading.

        Args:
            shots_to_deliver: List of shots to deliver
        """
        self.view.loading_widget.hide()

        for shot in shots_to_deliver:
            shot_widget = self.view.get_shot_widget(shot)
            self.view.shots_list_widget_layout.addWidget(shot_widget)

    def loading_shots_failed(self, error: str):
        """Runs when loading shots fails.

        Args:
            error: Error message from model
        """
        logger.error(f"Error while loading shots: {error}")
        self.view.loading_widget.hide()
        self.view.shots_list_widget_layout.addWidget(
            QtWidgets.QLabel("Error while loading shots. Please check logs!")
        )

    def open_delivery_folder(self):
        """Opens the delivery folder."""
        self.model.open_delivery_folder()

    def export_shots(self):
        """Runs the export function on the model."""
        self.view.final_validation_label.hide()
        self.model.export_shots(
            self.show_validation_error,
            self.update_progress_bar,
            self.show_validation_message,
        )

    def show_validation_error(self, shot: dict) -> None:
        """Sets the validation error text on the shot widget.

        Args:
            shot: Shot information to show validation error on
        """
        self.view.shot_widget_references[shot["id"]][
            "validation_label"
        ].setText(shot["validation_error"])
        self.view.shot_widget_references[shot["id"]][
            "validation_label"
        ].setStyleSheet("color: '#FF3E3E'; font: bold; font-size: 12px")
        self.view.final_validation_label.show()

    def show_validation_message(self, shot) -> None:
        """Sets the validation message on the shot widget.

        Args:
            shot: Shot to show validation message on
        """
        self.view.shot_widget_references[shot["id"]][
            "validation_label"
        ].setText(shot["validation_message"])
        self.view.shot_widget_references[shot["id"]][
            "validation_label"
        ].setStyleSheet("color: '#8BFF3E'; font: normal; font-size: 10px")

    def update_progress_bar(self, shot: dict) -> None:
        """Updates the progress bar on a shot.

        Args:
            shot: Shot to change progress bar on
        """
        self.view.shot_widget_references[shot["id"]][
            "shot_progress_bar"
        ].setValue(shot["frames_delivered"])
