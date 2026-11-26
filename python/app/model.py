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

"""Model for delivery tool, written by Mervin van Brakel 2024.

Reworked: shows every shot in the project (grouped per sequence) instead of
only shots with the 'Ready for Delivery' status. Delivering no longer depends
on, or changes, the shot status unless configured to do so.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from .qt_compat import QtCore


class ValidationError(Exception):
    """Gets raised when validation fails."""


def _natural_key(text: str) -> list:
    """Sort key that orders 'sh010' < 'sh020' < 'sh100' and '2' < '10'."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", text or "")
    ]


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
        self.shots = []

    # ------------------------------------------------------------------ misc
    def open_delivery_folder(self) -> None:
        """Finds the correct path and opens the delivery folder."""
        template = self._app.get_template("delivery_folder")

        roots = self.context.sgtk.roots
        root_name = self._app.get_setting("default_root")

        project_location = roots.get(root_name)
        delivery_location = template.apply_fields(project_location)

        os.makedirs(delivery_location, exist_ok=True)
        os.startfile(delivery_location)

    def get_project_code(self) -> str:
        """Gets the ShotGrid project code."""
        project = self.shotgrid_connection.find_one(
            "Project",
            [["id", "is", self.context.project["id"]]],
            ["sg_projectcode"],
        )
        return project["sg_projectcode"]

    def get_status_names(self) -> dict:
        """Maps status codes (e.g. 'rfd') to their full names."""
        try:
            statuses = self.shotgrid_connection.find("Status", [], ["code", "name"])
        except Exception:
            self.logger.exception("Could not load status names.")
            return {}
        return {status["code"]: status["name"] for status in statuses}

    # --------------------------------------------------------------- loading
    def get_all_shots(self) -> list[dict]:
        """Gets every shot in the project with its latest version info.

        Uses three batched ShotGrid queries (shots, versions, published files)
        instead of a query per shot, so large projects still load quickly.

        Returns:
            List of shot information dicts, sorted by sequence and shot.
        """
        self.logger.info("Loading all shots in project.")
        project_filter = [
            "project",
            "is",
            {"type": "Project", "id": self.context.project["id"]},
        ]

        sg_shots = self.shotgrid_connection.find(
            "Shot",
            [project_filter],
            ["code", "sg_sequence", "sg_status_list", "image"],
        )
        if not sg_shots:
            self.shots = []
            return self.shots

        project_code = self.get_project_code()
        shot_ids = [shot["id"] for shot in sg_shots]

        # Latest version per shot (one query, newest first).
        versions = self.shotgrid_connection.find(
            "Version",
            [
                project_filter,
                ["entity", "in", [{"type": "Shot", "id": i} for i in shot_ids]],
            ],
            ["entity", "published_files", "sg_first_frame", "sg_last_frame", "code", "image"],
            [{"field_name": "created_at", "direction": "desc"}],
        )
        latest_versions = {}
        for version in versions:
            shot_id = version["entity"]["id"]
            if shot_id not in latest_versions:
                latest_versions[shot_id] = version

        # First published file of each latest version (one query).
        publish_ids = [
            version["published_files"][0]["id"]
            for version in latest_versions.values()
            if version["published_files"]
        ]
        publishes = {}
        if publish_ids:
            for publish in self.shotgrid_connection.find(
                "PublishedFile",
                [["id", "in", publish_ids]],
                ["path", "version_number"],
            ):
                publishes[publish["id"]] = publish

        preselect_status = self._app.get_setting("preselect_status") or ""
        status_names = self.get_status_names()

        shots = []
        for sg_shot in sg_shots:
            sequence = (sg_shot.get("sg_sequence") or {}).get("name") or "No sequence"
            shot = {
                "id": sg_shot["id"],
                "sequence": sequence,
                "shot": sg_shot["code"],
                "status": sg_shot.get("sg_status_list"),
                "status_name": status_names.get(
                    sg_shot.get("sg_status_list"), sg_shot.get("sg_status_list") or ""
                ),
                "thumbnail_url": sg_shot.get("image"),
                "thumbnail_key": f"shot_{sg_shot['id']}",
                "project_code": project_code,
                "first_frame": None,
                "last_frame": None,
                "sequence_path": None,
                "version_number": None,
                "version_name": None,
                "load_error": None,
            }
            # Pre-tick shots that are ready for delivery: either the configured
            # status code, or any status whose name is "Ready for Delivery".
            shot["preselected"] = bool(
                (preselect_status and shot["status"] == preselect_status)
                or shot["status_name"].strip().lower() == "ready for delivery"
            )

            version = latest_versions.get(sg_shot["id"])
            if not version:
                shot["load_error"] = "No versions found for this shot."
            elif not version["published_files"]:
                shot["load_error"] = (
                    "Latest version has no published files (e.g. a playblast)."
                )
            else:
                publish = publishes.get(version["published_files"][0]["id"])
                path = (publish or {}).get("path") or {}
                if not path.get("local_path_windows"):
                    shot["load_error"] = "Published file has no local path."
                else:
                    shot["sequence_path"] = path["local_path_windows"]
                    shot["version_number"] = publish["version_number"]
                    shot["version_name"] = version.get("code")
                    shot["first_frame"] = version.get("sg_first_frame")
                    shot["last_frame"] = version.get("sg_last_frame")
                    if version.get("image"):
                        # Thumbnail of the version that gets delivered.
                        shot["thumbnail_url"] = version["image"]
                        shot["thumbnail_key"] = f"version_{version['id']}"

            shots.append(shot)

        shots.sort(key=lambda s: (_natural_key(s["sequence"]), _natural_key(s["shot"])))
        self.shots = shots
        self.logger.info(f"Loaded {len(shots)} shots.")
        return shots

    # ------------------------------------------------------------ validation
    def validate_shot(self, shot: dict) -> None:
        """Runs all validation checks on a shot.

        Raises:
            ValidationError: When the shot can't be delivered.
        """
        if shot["load_error"]:
            raise ValidationError(shot["load_error"])
        self.validate_filetype(shot)
        self.validate_all_frames_exist(shot)

    def validate_all_frames_exist(self, shot: dict) -> None:
        """Checks if all frames in the shot sequence exist."""
        if shot["first_frame"] is None or shot["last_frame"] is None:
            raise ValidationError(
                "Shot version is missing frame range data. Was it published correctly?"
            )

        for frame in range(shot["first_frame"], shot["last_frame"] + 1):
            try:
                frame_file_path = Path(shot["sequence_path"] % frame)
            except TypeError as error:
                raise ValidationError(
                    "Could not format filepath. Are the EXRs correctly linked to this shot version?"
                ) from error

            if not frame_file_path.is_file():
                self.logger.error(f"Could not find file at {frame_file_path}.")
                raise ValidationError(f"Can't find frame {frame}. Does it exist on disk?")

    def validate_filetype(self, shot: dict) -> None:
        """Checks that the linked file is not a reference MOV."""
        if shot["sequence_path"].lower().endswith(".mov"):
            raise ValidationError(
                "Linked version file is a reference MOV, not an EXR sequence."
            )

    # -------------------------------------------------------------- delivery
    def deliver_shot(self, shot: dict, progress_callback) -> None:
        """Hard-links the shot frames to the delivery folder.

        Args:
            shot: Shot information dict
            progress_callback: Called with (shot_id, frame) after every frame.

        Raises:
            ValidationError: When files already exist.
        """
        delivery_template = self._app.get_template("delivery_sequence")
        template_fields = {
            "Projectcode": shot["project_code"],
            "Sequence": shot["sequence"],
            "Shot": shot["shot"],
            "version": shot["version_number"],
        }

        delivery_path = Path(delivery_template.apply_fields(template_fields))
        delivery_path.parent.mkdir(parents=True, exist_ok=True)

        for frame in range(shot["first_frame"], shot["last_frame"] + 1):
            publish_file = Path(shot["sequence_path"] % frame)
            delivery_file = delivery_path.with_name(delivery_path.name % frame)
            try:
                os.link(publish_file, delivery_file)
            except FileExistsError as error:
                raise ValidationError(
                    "Files already exist. Has this version been delivered before?"
                ) from error
            progress_callback(shot["id"], frame)

        self.logger.info(f"Delivered {shot['sequence']} {shot['shot']} to {delivery_path.parent}.")

        # Optional: only touch the status when explicitly configured.
        if self._app.get_setting("set_delivered_status"):
            delivered_status = self._app.get_setting("delivered_status")
            self.shotgrid_connection.update(
                "Shot", shot["id"], {"sg_status_list": delivered_status}
            )


THUMBNAIL_CACHE = Path(tempfile.gettempdir()) / "nfa_deliveries_thumbnails"


class ThumbnailThread(QtCore.QThread):
    """Downloads shot thumbnails in the background, one by one.

    Thumbnails are cached per version, so reopening the app is fast.
    """

    thumbnail_ready = QtCore.Signal(int, str)  # shot id, local file path

    def __init__(self, model, shots: list[dict]):
        super().__init__()
        self.model = model
        self.shots = shots
        self._stopped = False

    def stop(self):
        self._stopped = True

    def run(self):
        import sgtk

        THUMBNAIL_CACHE.mkdir(parents=True, exist_ok=True)
        for shot in self.shots:
            if self._stopped:
                return
            url = shot.get("thumbnail_url")
            if not url:
                continue
            path = THUMBNAIL_CACHE / f"{shot['thumbnail_key']}.jpg"
            try:
                if not path.is_file() or path.stat().st_size == 0:
                    sgtk.util.download_url(
                        self.model.shotgrid_connection, url, str(path)
                    )
                self.thumbnail_ready.emit(shot["id"], str(path))
            except Exception as error:
                self.model.logger.warning(
                    f"Could not download thumbnail for {shot['shot']}: {error}"
                )


class LoadShotsThread(QtCore.QThread):
    """Loads shots on a separate thread so the UI doesn't freeze."""

    loading_shots_successful = QtCore.Signal(object)
    loading_shots_failed = QtCore.Signal(object)

    def __init__(self, model):
        super().__init__()
        self.model = model

    def run(self):
        try:
            self.loading_shots_successful.emit(self.model.get_all_shots())
        except Exception as error:
            self.model.logger.exception("Loading shots failed.")
            self.loading_shots_failed.emit(str(error))


class ExportShotsThread(QtCore.QThread):
    """Validates and delivers the selected shots on a separate thread.

    All UI updates go through signals, so they run safely on the UI thread.
    """

    shot_message = QtCore.Signal(int, str)  # shot id, message
    shot_error = QtCore.Signal(int, str)  # shot id, error
    shot_progress = QtCore.Signal(int, int)  # shot id, frame
    export_finished = QtCore.Signal(int, int)  # delivered, failed

    def __init__(self, model, shots: list[dict]):
        super().__init__()
        self.model = model
        self.shots = shots

    def run(self):
        delivered, failed = 0, 0
        for shot in self.shots:
            label = f"{shot['sequence']} {shot['shot']}"
            try:
                self.model.validate_shot(shot)
                self.shot_message.emit(shot["id"], "Validation passed, delivering...")
                self.model.deliver_shot(shot, self.shot_progress.emit)
                self.shot_message.emit(shot["id"], "Delivered!")
                delivered += 1
            except ValidationError as error:
                self.model.logger.error(f"{label}: {error}")
                self.shot_error.emit(shot["id"], str(error))
                failed += 1
            except Exception as error:
                self.model.logger.exception(f"{label}: unexpected error")
                self.shot_error.emit(
                    shot["id"], f"Unexpected error: {error}. Check the logs."
                )
                failed += 1
        self.export_finished.emit(delivered, failed)
