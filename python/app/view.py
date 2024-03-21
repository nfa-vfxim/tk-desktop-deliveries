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


"""View for delivery tool, written by Mervin van Brakel 2024"""

from pathlib import Path

from sgtk.platform.qt5 import QtCore, QtSvg, QtWidgets

SCRIPT_LOCATION: Path = Path(__file__).parent


class DeliveryView:
    """View for the ShotGrid delivery application.

    This view has all functions related to the Qt UI.
    """

    def __init__(self) -> None:
        self.shot_widget_references = {}

    def create_user_interface(self, main_widget: QtWidgets.QWidget):
        """Creates the UI of the window.

        Args:
            main_widget: The main application widget. We get this from the controller because
            I couldn't get it to work properly otherwise..
        """
        QtWidgets.QWidget.__init__(main_widget)

        self.layout = QtWidgets.QVBoxLayout(main_widget)
        self.layout.addWidget(self.get_explanation_widget())
        self.layout.addWidget(self.get_shots_list_widget())
        self.layout.addWidget(self.get_buttons_widget())

    @staticmethod
    def get_explanation_widget() -> QtWidgets.QWidget:
        """Gets the explanation widget of the layout.

        Returns:
            Widget containing explanation.
        """
        explanation_widget = QtWidgets.QWidget()
        explanation_widget_layout = QtWidgets.QVBoxLayout()
        explanation_widget.setLayout(explanation_widget_layout)

        explanation_label_1 = QtWidgets.QLabel(
            "Welcome to the delivery application!"
        )
        explanation_widget_layout.addWidget(explanation_label_1)

        explanation_label_2 = QtWidgets.QLabel(
            "This application is used to create the final return files that we send back to our editors."
        )
        explanation_widget_layout.addWidget(explanation_label_2)

        explanation_label_3 = QtWidgets.QLabel(
            "Only shots with the status 'Ready for Delivery' show up in this program."
        )
        explanation_widget_layout.addWidget(explanation_label_3)

        explanation_label_4 = QtWidgets.QLabel(
            "This program only exports the latest version of the shots, so make sure shots are published correctly."
        )
        explanation_widget_layout.addWidget(explanation_label_4)

        return explanation_widget

    def get_shots_list_widget(self) -> QtWidgets.QWidget:
        """Gets the shot list widget of the layout.

        Returns:
            Widget containing shot list.
        """
        self.shots_list_scroll_area = QtWidgets.QScrollArea()
        self.shots_list_widget = QtWidgets.QWidget()
        self.shots_list_widget_layout = QtWidgets.QVBoxLayout()
        self.shots_list_widget.setLayout(self.shots_list_widget_layout)

        self.shots_list_widget.setStyleSheet("background-color:#2A2A2A;")
        self.shots_list_widget_layout.addWidget(self.get_loading_widget())

        self.shots_list_scroll_area.setWidget(self.shots_list_widget)
        self.shots_list_scroll_area.setWidgetResizable(True)

        return self.shots_list_scroll_area

    def get_buttons_widget(self) -> QtWidgets.QWidget:
        """Gets the buttons widget of the layout.

        Returns:
            Widget containing buttons.
        """
        buttons_widget = QtWidgets.QWidget()
        buttons_widget_layout = QtWidgets.QVBoxLayout()
        buttons_widget.setLayout(buttons_widget_layout)

        self.final_validation_label = QtWidgets.QLabel(
            "Some shots are not exported due to errors!"
        )
        self.final_validation_label.hide()
        self.final_validation_label.setStyleSheet(
            "color: '#FF3E3E'; font: bold; font-size: 12px"
        )
        buttons_widget_layout.addWidget(self.final_validation_label)

        self.reload_button = QtWidgets.QPushButton("Reload shot list")
        buttons_widget_layout.addWidget(self.reload_button)

        self.export_shots_button = QtWidgets.QPushButton("Export shots")
        buttons_widget_layout.addWidget(self.export_shots_button)

        self.open_delivery_folder_button = QtWidgets.QPushButton(
            "Open delivery folder"
        )
        buttons_widget_layout.addWidget(self.open_delivery_folder_button)

        return buttons_widget

    def get_loading_widget(self) -> QtWidgets.QWidget:
        """Gets the loading widget for the layout.

        Returns:
            Widget containing loading widgets.
        """
        self.loading_widget = QtWidgets.QWidget()
        loading_widget_layout = QtWidgets.QVBoxLayout()
        loading_widget_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.loading_widget.setLayout(loading_widget_layout)

        loading_spinner = QtSvg.QSvgWidget(
            str(
                SCRIPT_LOCATION / "../.." / "resources" / "loading_spinner.svg"
            )
        )
        loading_spinner.setFixedSize(100, 100)
        loading_widget_layout.addWidget(
            loading_spinner, 0, QtCore.Qt.AlignHCenter
        )

        return self.loading_widget

    def get_shot_widget(self, shot: dict) -> QtWidgets.QWidget:
        """Gets the shot widget for the layout. It also stores this
        widget in the reference list so we can update its UI later.

        Args:
            shot: Shot information dictionary

        Returns:
            Widget for shot information.
        """
        self.shot_widget_references[shot["id"]] = {}

        self.shot_widget_references[shot["id"]]["widget"] = QtWidgets.QWidget()
        shot_widget_vertical_layout = QtWidgets.QVBoxLayout()
        self.shot_widget_references[shot["id"]]["widget"].setLayout(
            shot_widget_vertical_layout
        )

        shot_name_label = QtWidgets.QLabel(
            f"Sequence {shot['sequence']} - Shot {shot['shot']}."
        )
        shot_name_label.setStyleSheet("font: bold; font-size: 14px")
        shot_widget_vertical_layout.addWidget(shot_name_label)

        shot_info_label = QtWidgets.QLabel(
            f"Frames {shot['first_frame']} - {shot['last_frame']}. Version {shot['version_number']}."
        )
        shot_info_label.setStyleSheet("font-size: 12px")
        shot_widget_vertical_layout.addWidget(shot_info_label)

        self.shot_widget_references[shot["id"]]["validation_label"] = (
            QtWidgets.QLabel("Shot ready for export!")
        )
        self.shot_widget_references[shot["id"]][
            "validation_label"
        ].setStyleSheet("color: '#8BFF3E'; font-size: 10px;")
        shot_widget_vertical_layout.addWidget(
            self.shot_widget_references[shot["id"]]["validation_label"]
        )

        self.shot_widget_references[shot["id"]][
            "shot_progress_bar"
        ] = QtWidgets.QProgressBar()
        self.shot_widget_references[shot["id"]][
            "shot_progress_bar"
        ].setMinimum(shot["first_frame"])
        self.shot_widget_references[shot["id"]][
            "shot_progress_bar"
        ].setMaximum(shot["last_frame"])
        self.shot_widget_references[shot["id"]][
            "shot_progress_bar"
        ].setStyleSheet(
            "QProgressBar::chunk {background-color: #8BFF3E;} QProgressBar {color: black; background-color: #444444; text-align: center;}"
        )
        shot_widget_vertical_layout.addWidget(
            self.shot_widget_references[shot["id"]]["shot_progress_bar"]
        )

        return self.shot_widget_references[shot["id"]]["widget"]
