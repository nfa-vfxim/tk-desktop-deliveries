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


class AlreadyDelivered(Exception):
    """Gets raised when this version is already in the delivery folder."""


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

        Uses a few batched ShotGrid queries instead of a query per shot, so
        large projects still load quickly.

        Returns:
            List of shot information dicts, sorted by sequence and shot.
        """
        self.logger.info("Loading all shots in project.")
        project_filter = [
            "project",
            "is",
            {"type": "Project", "id": self.context.project["id"]},
        ]

        status_names = self.get_status_names()
        hidden_statuses = set(self._app.get_setting("hidden_statuses") or [])

        sg_shots = [
            shot
            for shot in self.shotgrid_connection.find(
                "Shot",
                [project_filter],
                ["code", "sg_sequence", "sg_status_list", "image"],
            )
            if shot.get("sg_status_list") not in hidden_statuses
            and status_names.get(shot.get("sg_status_list"), "").strip().lower() != "omit"
        ]
        if not sg_shots:
            self.shots = []
            return self.shots

        project_code = self.get_project_code()
        shot_entities = [{"type": "Shot", "id": shot["id"]} for shot in sg_shots]

        # Latest version per shot (one query, newest first).
        versions = self.shotgrid_connection.find(
            "Version",
            [project_filter, ["entity", "in", shot_entities]],
            ["entity", "published_files", "sg_first_frame", "sg_last_frame", "code", "image"],
            [{"field_name": "created_at", "direction": "desc"}],
        )
        latest_versions = {}
        for version in versions:
            latest_versions.setdefault(version["entity"]["id"], version)

        # ALL published files of each latest version (one query). A version
        # often has both a review MOV and the EXR sequence linked.
        publish_ids = [
            publish["id"]
            for version in latest_versions.values()
            for publish in version["published_files"] or []
        ]
        publishes = {}
        if publish_ids:
            for publish in self.shotgrid_connection.find(
                "PublishedFile",
                [["id", "in", publish_ids]],
                ["path", "version_number"],
            ):
                publishes[publish["id"]] = publish

        # Fallback: newest EXR publish on the shot itself, for shots whose
        # latest version only links a MOV (one query).
        fallback_exrs = {}
        for publish in self.shotgrid_connection.find(
            "PublishedFile",
            [project_filter, ["entity", "in", shot_entities], ["path_cache", "contains", ".exr"]],
            ["entity", "path", "version_number", "version"],
            [{"field_name": "version_number", "direction": "desc"},
             {"field_name": "created_at", "direction": "desc"}],
        ):
            if publish.get("entity") and _local_path(publish):
                fallback_exrs.setdefault(publish["entity"]["id"], publish)

        preselect_status = self._app.get_setting("preselect_status") or ""

        shots = []
        for sg_shot in sg_shots:
            sequence = (sg_shot.get("sg_sequence") or {}).get("name") or "No sequence"
            status = sg_shot.get("sg_status_list")
            shot = {
                "id": sg_shot["id"],
                "sequence": sequence,
                "shot": sg_shot["code"],
                "status": status,
                "status_name": status_names.get(status, status or ""),
                "thumbnail_url": sg_shot.get("image"),
                "thumbnail_key": f"shot_{sg_shot['id']}",
                "project_code": project_code,
                "first_frame": None,
                "last_frame": None,
                "sequence_path": None,
                "version_number": None,
                "version_name": None,
                "load_error": None,  # shot is hidden from the list
                "blocked": None,  # shot is listed but can't be ticked
                "note": None,  # yellow info shown in the Result column
            }
            shot["preselected"] = bool(
                (preselect_status and status == preselect_status)
                or shot["status_name"].strip().lower() == "ready for delivery"
            )

            version = latest_versions.get(sg_shot["id"])
            if not version:
                shot["load_error"] = "No versions found for this shot."
                shots.append(shot)
                continue

            shot["version_name"] = version.get("code")
            shot["first_frame"] = version.get("sg_first_frame")
            shot["last_frame"] = version.get("sg_last_frame")
            if version.get("image"):
                # Thumbnail of the version that gets delivered.
                shot["thumbnail_url"] = version["image"]
                shot["thumbnail_key"] = f"version_{version['id']}"

            version_publishes = [
                publishes[p["id"]]
                for p in version["published_files"] or []
                if p["id"] in publishes and _local_path(publishes[p["id"]])
            ]
            exr = next((p for p in version_publishes if _is_exr(p)), None)

            if exr:
                shot["sequence_path"] = _local_path(exr)
                shot["version_number"] = exr["version_number"]
            elif shot["id"] in fallback_exrs:
                exr = fallback_exrs[shot["id"]]
                shot["sequence_path"] = _local_path(exr)
                shot["version_number"] = exr["version_number"]
                shot["note"] = (
                    f"Latest version has no EXRs; delivered older EXR publish "
                    f"v{exr['version_number']:03d}."
                )
            elif version_publishes:
                shot["blocked"] = (
                    "Only a reference MOV is published and no older EXR publish exists."
                )
            else:
                shot["load_error"] = "Latest version has no published files."

            shots.append(shot)

        shots.sort(key=lambda s: (_natural_key(s["sequence"]), _natural_key(s["shot"])))
        self.shots = shots
        self.logger.info(f"Loaded {len(shots)} shots.")
        return shots

    # ------------------------------------------------------------ validation
    def find_frames_on_disk(self, sequence_path: str) -> list[int]:
        """Returns the sorted frame numbers that exist for a sequence path.

        Supports %04d, %d and #### frame patterns.
        """
        folder = Path(sequence_path).parent
        name = Path(sequence_path).name
        match = re.search(r"%0?(\d*)d|#+", name)
        if not match:
            raise ValidationError("Published path is not a frame sequence.")
        prefix, suffix = name[: match.start()], name[match.end() :]
        pattern = re.compile(
            "^" + re.escape(prefix) + r"(-?\d+)" + re.escape(suffix) + "$", re.IGNORECASE
        )
        if not folder.is_dir():
            raise ValidationError(f"Publish folder doesn't exist: {folder}")
        frames = []
        for entry in os.scandir(folder):
            found = pattern.match(entry.name)
            if found and entry.is_file():
                frames.append(int(found.group(1)))
        return sorted(frames)

    def validate_shot(self, shot: dict) -> list[str]:
        """Checks the shot and decides which frames to deliver.

        Returns:
            Warnings (yellow) for things that don't stop the delivery.

        Raises:
            ValidationError: When the shot can't be delivered.
        """
        if shot["load_error"] or shot["blocked"]:
            raise ValidationError(shot["load_error"] or shot["blocked"])
        if not _is_exr({"path": {"local_path_windows": shot["sequence_path"]}}):
            raise ValidationError("Linked file is not an EXR sequence.")

        frames = self.find_frames_on_disk(shot["sequence_path"])
        if not frames:
            raise ValidationError(
                f"No EXR frames found on disk in {Path(shot['sequence_path']).parent}"
            )
        shot["frames_on_disk"] = frames

        warnings = []

        first, last = shot["first_frame"], shot["last_frame"]
        disk_range = f"{frames[0]}-{frames[-1]}"
        if first is None or last is None:
            warnings.append(f"No frame range on version; delivered {disk_range}.")
        else:
            expected = set(range(first, last + 1))
            missing = len(expected - set(frames))
            if frames[0] != first or frames[-1] != last or missing:
                text = f"Frame range doesn't match: expected {first}-{last}, on disk {disk_range}"
                if missing:
                    text += f", {missing} missing"
                warnings.append(text + ".")
        return warnings

    # -------------------------------------------------------------- delivery
    def deliver_shot(self, shot: dict, progress_callback) -> None:
        """Hard-links the frames found on disk to the delivery folder.

        Args:
            shot: Shot information dict (validated, so it has frames_on_disk)
            progress_callback: Called with (shot_id, done, total) after every frame.

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

        source = Path(shot["sequence_path"])
        source_pattern = re.compile(r"%0?(\d*)d|#+")
        frames = shot["frames_on_disk"]
        pairs = [
            (
                source.with_name(
                    source_pattern.sub(lambda m, f=frame: _format_frame(m, f), source.name, count=1)
                ),
                delivery_path.with_name(delivery_path.name % frame),
            )
            for frame in frames
        ]

        # Leave an existing delivery of this version alone.
        if any(target.exists() for _, target in pairs):
            raise AlreadyDelivered()

        for index, (publish_file, delivery_file) in enumerate(pairs, 1):
            os.link(publish_file, delivery_file)
            progress_callback(shot["id"], index, len(frames))

        self.logger.info(f"Delivered {shot['sequence']} {shot['shot']} to {delivery_path.parent}.")

        # Optional: only touch the status when explicitly configured.
        if self._app.get_setting("set_delivered_status"):
            delivered_status = self._app.get_setting("delivered_status")
            self.shotgrid_connection.update(
                "Shot", shot["id"], {"sg_status_list": delivered_status}
            )


def _local_path(publish: dict) -> str:
    return ((publish or {}).get("path") or {}).get("local_path_windows") or ""


def _is_exr(publish: dict) -> bool:
    return _local_path(publish).lower().endswith(".exr")


def _format_frame(match, frame: int) -> str:
    """Formats a frame number like the %04d / #### token it replaces."""
    token = match.group(0)
    if token.startswith("#"):
        padding = len(token)
    else:
        padding = int(match.group(1) or 0)
    return str(frame).zfill(padding)


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
    shot_warning = QtCore.Signal(int, str)  # shot id, warning (delivered anyway)
    shot_error = QtCore.Signal(int, str)  # shot id, error
    shot_progress = QtCore.Signal(int, int, int)  # shot id, done, total
    export_finished = QtCore.Signal(int, int, int)  # delivered, with warnings, failed

    def __init__(self, model, shots: list[dict]):
        super().__init__()
        self.model = model
        self.shots = shots

    def run(self):
        delivered, warned, failed = 0, 0, 0
        for shot in self.shots:
            label = f"{shot['sequence']} {shot['shot']}"
            try:
                warnings = self.model.validate_shot(shot)
                self.shot_message.emit(shot["id"], "Delivering...")
                self.model.deliver_shot(shot, self.shot_progress.emit)
                delivered += 1
                if shot["note"]:
                    # Delivered, but not the latest version: red so it stands out.
                    warned += 1
                    text = " ".join([shot["note"]] + warnings)
                    self.model.logger.warning(f"{label}: {text}")
                    self.shot_error.emit(shot["id"], text)
                elif warnings:
                    warned += 1
                    text = "Delivered, but: " + " ".join(warnings)
                    self.model.logger.warning(f"{label}: {text}")
                    self.shot_warning.emit(shot["id"], text)
                else:
                    self.shot_message.emit(shot["id"], "Delivered!")
            except AlreadyDelivered:
                self.model.logger.info(f"{label}: already delivered, skipped.")
                self.shot_message.emit(shot["id"], "Already delivered.")
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
        self.export_finished.emit(delivered, warned, failed)
