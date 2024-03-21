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


"""Model for delivery tool, written by Mervin van Brakel 2024"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from sgtk.platform.qt5 import QtCore


class ValidationError(Exception):
    """Gets raised when validation fails."""


class DeliveryModel:
    def __init__(self, app, logger) -> None:
        """Initializes the model.

        Args:
            app: ShotGrid app
            logger: ShotGrid logger
        """
        self._app = app
        self.context = app.context
        self.shotgrid_connection = app.shotgun
        self.logger = logger
        self.shots_to_deliver = None

    def open_delivery_folder(self) -> None:
        """Finds the correct path and opens the delivery folder."""
        template = self._app.get_template("delivery_folder")

        roots = self.context.sgtk.roots
        root_name = self._app.get_setting("default_root")

        project_location = roots.get(root_name)
        delivery_location = template.apply_fields(project_location)

        os.startfile(delivery_location)

    def load_shots(
        self,
        loading_shots_successful_function: Callable,
        loading_shots_failed_function: Callable,
    ) -> None:
        """Loads shots on a separate thread.

        Args:
            loading_shots_successful_function: Function that gets called when loading shots is successful.
            loading_shots_failed_function: Function that gets called when loading shots failed.
        """
        self.load_shots_thread = LoadShotsThread(self)

        self.load_shots_thread.loading_shots_successful.connect(
            loading_shots_successful_function
        )
        self.load_shots_thread.loading_shots_failed.connect(
            loading_shots_failed_function
        )

        self.load_shots_thread.start()

    def get_shots_to_deliver(self) -> list[dict]:
        """Gets a list of shots that are ready for delivery.

        Returns:
            List of shot information dictionaries.
        """
        self.logger.info("Starting 'ready for delivery' search.")
        project_id = self.context.project["id"]
        delivery_status = self._app.get_setting("delivery_status")

        filters = [
            [
                "project",
                "is",
                {"type": "Project", "id": project_id},
            ],
            ["sg_status_list", "is", delivery_status],
        ]

        columns = [
            "sg_sequence",
            "code",
        ]

        shots_to_deliver = self.shotgrid_connection.find(
            "Shot", filters, columns
        )

        self.shots_to_deliver = self.get_shots_information_list(
            shots_to_deliver
        )
        return self.shots_to_deliver

    def get_latest_shot_version(self, shot_information: dict) -> dict:
        """Gets the latest version of the shot with some handy information.

        Args:
            shot_information: Information on shot to get version for

        Returns:
            Latest version of shot
        """
        filters = [
            ["entity", "is", {"type": "Shot", "id": shot_information["id"]}],
        ]

        columns = [
            "published_files",
            "sg_first_frame",
            "sg_last_frame",
        ]

        sorting = [
            {
                "column": "created_at",
                "direction": "desc",
            }
        ]

        return self.shotgrid_connection.find_one(
            "Version",
            filters,
            columns,
            sorting,
        )

    def get_shot_version_published_file(
        self, latest_shot_version: dict
    ) -> dict:
        """Gets the correct published files associates with this version.

        Args:
            latest_shot_version: Latest shot version information

        Returns:
            Published files
        """
        publishes = latest_shot_version["published_files"]

        filters = [
            ["id", "is", publishes[0]["id"]],
        ]

        columns = ["path", "published_file_type", "version_number"]

        return self.shotgrid_connection.find_one(
            "PublishedFile",
            filters,
            columns,
        )

    def get_project_code(self) -> str:
        """Gets the ShotGrid project code.

        Returns:
            Project code"""
        project_id = self.context.project["id"]
        filters = [
            [
                "id",
                "is",
                project_id,
            ]
        ]

        columns = ["sg_projectcode"]
        project = self.shotgrid_connection.find_one(
            "Project", filters, columns
        )

        return project["sg_projectcode"]

    def get_shots_information_list(self, shots_to_deliver: list) -> list[dict]:
        """This function takes a list of shots and adds all the extra
        information we need for the rest of the program to function.

        Args:
            shots_to_deliver: List of shots to deliver

        Returns:
            List of shot information dicts
        """
        shots_information_list = []

        for shot in shots_to_deliver:
            shot_information = {}

            shot_information["sequence"] = shot["sg_sequence"]["name"]
            shot_information["shot"] = shot["code"]
            shot_information["id"] = shot["id"]

            latest_shot_version = self.get_latest_shot_version(
                shot_information
            )

            shot_information["first_frame"] = (
                latest_shot_version["sg_first_frame"]
                if latest_shot_version["sg_first_frame"]
                else -1
            )

            shot_information["last_frame"] = (
                latest_shot_version["sg_last_frame"]
                if latest_shot_version["sg_last_frame"]
                else 0
            )

            published_file = self.get_shot_version_published_file(
                latest_shot_version
            )
            shot_information["sequence_path"] = published_file["path"][
                "local_path_windows"
            ]
            shot_information["version_number"] = published_file[
                "version_number"
            ]
            shot_information["project_code"] = self.get_project_code()

            shots_information_list.append(shot_information)

        return shots_information_list

    def export_shots(
        self,
        show_validation_error: Callable,
        update_progress_bars: Callable,
        show_validation_message: Callable,
    ) -> None:
        """Starts the shot export thread.

        Args:
            show_validation_error: Function for showing validation errors
            update_progress_bars: Function for updating progress bars
            show_validation_message: Function for showing validation messages
        """
        self.validate_shots_thread = ExportShotsThread(
            self,
            show_validation_error,
            update_progress_bars,
            show_validation_message,
        )
        self.validate_shots_thread.start()

    def validate_all_shots(
        self,
        show_validation_error: Callable,
        show_validation_message: Callable,
    ) -> list:
        """Goes over all the shots and checks if all frames exist.

        Args:
            show_validation_error: Function for showing validation errors
            show_validation_message: Function for showing validation messages

        Returns:
            List of successfully validated shots

        Raises:
            ValidationError: Error when validation fails.
        """
        self.logger.info("Starting validation of shots.")

        successfully_validated_shots = []
        for shot in self.shots_to_deliver:
            self.logger.info(
                f"Validating sequence {shot['sequence']}, shot {shot['shot']}."
            )
            try:
                self.validate_filetype(shot)
                self.validate_all_frames_exist(shot)
                successfully_validated_shots.append(shot)
                self.logger.info("Validation passed.")
                shot["validation_message"] = (
                    "Initial validation checks passed!"
                )
                show_validation_message(shot)

            except ValidationError as error_message:
                self.logger.error(f"Validation failed: {error_message}")
                shot["validation_error"] = str(error_message)

                # This is kinda sketchy, I know
                show_validation_error(shot)

        return successfully_validated_shots

    def validate_all_frames_exist(self, shot: dict) -> None:
        """Checks if all frames in the shot sequence exist

        Args:
            shot: Shot information dict

        Raises:
            ValidationError: Error when validation fails
        """
        if shot["first_frame"] == -1:
            self.logger.error(
                "Missing frame range data. Please check if first_frame and last_frame are set properly on the version info."
            )
            error_message = "Shot version is missing frame range data. Was it published correctly?"
            raise ValidationError(error_message)

        for frame in range(shot["first_frame"], shot["last_frame"]):

            try:
                frame_file_path = Path(shot["sequence_path"] % frame)
            except TypeError as e:
                self.logger.error(
                    "Filepath formatting failed. Probably because linked file on this version is not an EXR sequence."
                )
                error_message = "Could not format filepath. Are the EXRs correctly linked to this shot version?"
                raise ValidationError(error_message) from e

            if not frame_file_path.is_file():
                self.logger.error(f"Could not find file at {frame_file_path}.")
                error_message = (
                    f"Can't find frame {frame}. Does it exist on disk?"
                )
                raise ValidationError(error_message)

    def validate_filetype(self, shot: dict) -> None:
        """Checks if the filetype is an EXR.

        Args:
            shot: Shot information

        Raises:
            ValidationError: Error if validation fails.
        """
        if shot["sequence_path"].endswith(".mov"):
            self.logger.error(
                "Found MOV on latest version, not an EXR. This often happens because the ingest reference version is still the latest version."
            )
            error_message = (
                "Linked version file is a reference MOV, not an EXR sequence."
            )
            raise ValidationError(error_message)

    def deliver_shot(
        self,
        shot: dict,
        show_validation_error: Callable,
        show_validation_message: Callable,
        update_progress_bars: Callable,
    ) -> None:
        """Copies the shot to the right folder with the right naming conventions.

        Args:
            shot: Shot information dict
            show_validation_error: Function for showing validation errors
            show_validation_message: Function for showing validation message,
            update_progress_bars: Function for updating the progress bars
        """
        try:
            delivery_template = self._app.get_template("delivery_sequence")

            template_fields = {
                "Projectcode": shot["project_code"],
                "Sequence": shot["sequence"],
                "Shot": shot["shot"],
                "version": shot["version_number"],
            }

            delivery_path = Path(
                delivery_template.apply_fields(template_fields)
            )
            delivery_folder = delivery_path.parent

            if not delivery_folder.is_dir():
                self.logger.info(
                    f"Creating folder for delivery {delivery_folder}."
                )
                delivery_folder.mkdir(parents=True, exist_ok=True)

            for frame in range(shot["first_frame"], shot["last_frame"] + 1):
                publish_file = Path(shot["sequence_path"] % frame)
                delivery_file = delivery_path.with_name(
                    delivery_path.name % frame
                )

                os.link(publish_file, delivery_file)

                shot["frames_delivered"] = frame
                update_progress_bars(shot)

            self.logger.info(
                f"Finished linking {publish_file} to {delivery_file}."
            )

            delivered_status = self._app.get_setting("delivered_status")
            data = {
                "sg_status_list": delivered_status,
            }
            self.shotgrid_connection.update("Shot", shot["id"], data)

            shot["validation_message"] = "Export finished!"
            show_validation_message(shot)

        except FileExistsError:
            self.logger.error(
                "Files already exist. Has this shot been exported before?"
            )
            shot["validation_error"] = (
                "Files already exist. Has this shot been exported before?"
            )
            show_validation_error(shot)

        except Exception as error:
            self.logger.error(str(error))
            shot["validation_error"] = (
                "Unexpected error occurred while copying files, please check logs!"
            )
            show_validation_error(shot)


class ExportShotsThread(QtCore.QThread):
    """Class for exporting shots on a separate thread
    so the UI doesn't freeze."""

    def __init__(
        self,
        model,
        show_validation_error,
        update_progress_bars,
        show_validation_message,
    ):
        super().__init__()
        self.model = model
        self.show_validation_error = show_validation_error
        self.update_progress_bars = update_progress_bars
        self.show_validation_message = show_validation_message

    def run(self):
        validated_shots = self.model.validate_all_shots(
            self.show_validation_error, self.show_validation_message
        )

        for shot in validated_shots:
            self.model.deliver_shot(
                shot,
                self.show_validation_error,
                self.show_validation_message,
                self.update_progress_bars,
            )


class LoadShotsThread(QtCore.QThread):
    """Class for loading shots on a separate thread
    so the UI doesn't freeze."""

    loading_shots_successful = QtCore.Signal(object)
    loading_shots_failed = QtCore.Signal(object)

    def __init__(self, model):
        super().__init__()
        self.model = model

    def run(self):
        try:
            shots_to_deliver = self.model.get_shots_to_deliver()
            self.loading_shots_successful.emit(shots_to_deliver)
        except Exception as error:
            self.loading_shots_failed.emit(str(error))
