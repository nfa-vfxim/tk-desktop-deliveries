# MIT License

# Copyright (c) 2022 Netherlands Film Academy

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


import sgtk
import os
import sys

from sgtk.platform.qt import QtCore, QtGui
from .ui.dialog import Ui_Dialog

# standard toolkit logger
logger = sgtk.platform.get_logger(__name__)


def show_dialog(app_instance):
    """
    Shows the main dialog window.
    """

    app_instance.engine.show_dialog("Deliveries", app_instance, AppDialog)


class AppDialog(QtGui.QWidget):
    """
    Main application dialog window
    """

    def __init__(self):
        """
        Constructor
        """
        # first, call the base class and let it do its thing.
        QtGui.QWidget.__init__(self)

        # now load in the UI that was created in the UI designer
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.operating_system = sys.platform

        # Getting current app instance and context
        self._app = sgtk.platform.current_bundle()
        self.sg = self._app.shotgun

        self.context = self._app.context

        # logging happens via a standard toolkit logger
        logger.info("Launching Delivery Application...")

        self.setup_interface()

        self.ui.reload.clicked.connect(self.setup_interface)
        self.ui.deliver.clicked.connect(self.set_ready_for_delivery)
        self.ui.open_folder.clicked.connect(self.open_delivery_folder)

    def setup_interface(self):
        """This function will initially setup the list widget
        to show shots.
        """
        # Clear widget
        self.ui.deliveryItems.clear()

        # Get shots
        shots = self.__get_delivery_shots()

        # Convert to readable list
        readable_shots = self.__create_readable_list(shots)

        if len(readable_shots) > 0:
            # Edit list widget
            self.ui.deliveryItems.addItems(readable_shots)

    def open_delivery_folder(self):
        """Function to open the delivery folder in the matching
        operating system.
        """
        # Get template
        template = self._app.get_template("delivery_folder")

        # Get project location
        roots = self.context.sgtk.roots
        root_name = self._app.get_setting("default_root")
        project_location = roots.get(root_name)
        project_location = project_location.replace(os.sep, "/")

        # Generate delivery location
        delivery_location = template.apply_fields(project_location)
        delivery_location = delivery_location.replace(os.sep, "/")

        # Detect operating system to create correct command
        operating_system = self.operating_system

        # Open folder in file system
        if operating_system == "darwin":
            os.system("open %s" % delivery_location)

        elif operating_system == "win32":
            delivery_location = os.path.normpath(delivery_location)
            os.system("explorer %s" % delivery_location)

        elif operating_system == "linux":
            os.system('xdg-open "%s"' % delivery_location)

    def set_ready_for_delivery(self):
        """This function will collect the shots to deliver, validate it,
        and move it to the delivery folder.
        """

        # Get shots
        shots = self.__get_delivery_shots()

        # Iterate trough every shot
        for shot in shots:

            # Get shot information
            sequence_name = shot.get("sg_sequence")
            sequence_name = sequence_name.get("name")

            shot_name = shot.get("code")
            shot_id = shot.get("id")

            # Find latest version
            filters = [
                ["entity", "is", {"type": "Shot", "id": shot_id}],
            ]

            # TODO add support for mattes
            columns = [
                "published_files",
                "mattes",
                "sg_first_frame",
                "sg_last_frame",
            ]

            sorting = [
                {
                    "column": "created_at",
                    "direction": "desc",
                }
            ]

            # Get verision
            latest_version = self.sg.find_one(
                "Version",
                filters,
                columns,
                sorting,
            )

            # Get version information
            first_frame = latest_version.get("sg_first_frame")
            last_frame = latest_version.get("sg_last_frame")

            # Get publishes
            publishes = latest_version.get("published_files")
            for publish in publishes:

                # Get publish information, via this way
                # we can add support for extra mattes

                publish_id = publish.get("id")

                filters = [
                    ["id", "is", publish_id],
                ]

                columns = ["path", "published_file_type", "version_number"]

                # Get publish
                publish = self.sg.find_one(
                    "PublishedFile",
                    filters,
                    columns,
                )

                # Get path to sequence path
                sequence_path = publish.get("path")

                # Every os has a different path, so get the correct path
                operating_system = self.operating_system

                # Probably this will match the studio's operating system path
                if operating_system == "darwin":
                    sequence_path = sequence_path.get("local_path_mac")

                elif operating_system == "win32":
                    sequence_path = sequence_path.get("local_path_windows")
                    sequence_path = sequence_path.replace(os.sep, "/")

                elif operating_system == "linux":
                    sequence_path = sequence_path.get("local_path_linux")

                # Validate if every file is existing to deliver
                validated = self.__validate_sequence(
                    sequence_path=sequence_path,
                    first_frame=first_frame,
                    last_frame=last_frame,
                )

                if validated:
                    # Hard link to the delivery folder to save
                    # time and disk space
                    self.__deliver_sequence(
                        publish=publish,
                        sequence_name=sequence_name,
                        shot_name=shot_name,
                        sequence_path=sequence_path,
                        first_frame=first_frame,
                        last_frame=last_frame,
                        shot_id=shot_id,
                    )

                # Update interface
                self.setup_interface()

    def __deliver_sequence(
        self,
        publish,
        sequence_name,
        shot_name,
        sequence_path,
        first_frame,
        last_frame,
        shot_id,
    ):
        """This function will hard link the provided sequence path to the
        delivery folder.

        Args:
            publish (dict): containing all publish information
            sequence_name (str): sequence code name
            shot_name (str): shot code name
            sequence_path (str): publish file path to the sequence
            first_frame (float): first frame to deliver
            last_frame (float): last frame to deliver
            shot_id (int): id of the shot in ShotGrid

        Returns:
            bool: True if succeeded false if failed
        """

        try:
            delivery_template = self._app.get_template("delivery_sequence")

            # Get project code
            project_id = self.context.project["id"]
            filters = [
                [
                    "id",
                    "is",
                    project_id,
                ]
            ]

            columns = ["sg_projectcode"]
            project = self.sg.find_one("Project", filters, columns)

            project_code = project.get("sg_projectcode")
            version_number = publish.get("version_number")

            fields = {}

            fields["projectcode"] = project_code
            fields["Sequence"] = sequence_name
            fields["Shot"] = shot_name
            fields["version"] = version_number

            delivery_path = delivery_template.apply_fields(fields)
            delivery_path = delivery_path.replace(os.sep, "/")

            delivery_folder = os.path.dirname(delivery_path)

            if not os.path.isdir(delivery_folder):
                logger.info(
                    "Creating folder for delivery %s." % delivery_folder
                )
                os.makedirs(delivery_folder)

            for frame in range(first_frame, last_frame):
                publish_file = sequence_path % frame
                delivery_file = delivery_path % frame

                logger.info(
                    "Hard linking %s to %s." % (publish_file, delivery_file)
                )

                os.link(publish_file, delivery_file)

            # Update status

            delivered_status = self._app.get_setting("delivered_status")
            data = {
                "sg_status_list": delivered_status,
            }
            self.sg.update("Shot", shot_id, data)

        except Exception as error:
            logger.info("Something went wrong... %s" % str(error))
            return False

        return True

    @staticmethod
    def __validate_sequence(sequence_path, first_frame, last_frame):
        # Lets check if every frame is existing in the frame sequence
        is_valid = True

        logger.info("Got %s" % sequence_path)

        for frame in range(first_frame, last_frame):
            file_path = os.path.isfile(sequence_path % frame)
            logger.info("Checking %s with frame %f" % (sequence_path, frame))
            if not file_path:
                is_valid = False
                logger.info(
                    "File sequence is not complete, please re-render it "
                    "again in the full frame range."
                )

                return is_valid

        return is_valid

    def __get_delivery_shots(self):
        """Function to get shots from ShotGrid
        with the status code "rfd" (ready for delivery).

        If the status is active on the specific shot, it will be added
        to the list.

        Returns:
            list: containing shots with correct status
            example:    [
                            {
                                "type": "Shot",
                                "id": 7563,
                                "sg_sequence": {"id": 4518, "name": "010", "type": "Sequence"},
                                "code": "0010",
                            }
                        ]
        """
        # Get current context
        project_id = self.context.project["id"]

        # Get the shortcode for the delivery status
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

        # Find shots using provided parameters
        shots = self.sg.find("Shot", filters, columns)

        return shots

    def __create_readable_list(self, shots):
        """This function will convert the list from ShotGrid
        to a somewhat more readable one to create the list in the
        user interface.

        Args:
            shots (list): containing all data regarding shots

        Returns:
            list: with readable information on shots to process
        """
        readable_list = []

        for shot in shots:
            sequence_name = shot.get("sg_sequence")
            sequence_name = sequence_name.get("name")

            shot_name = shot.get("code")

            readable_shot = "Sequence: %s, shot: %s" % (
                sequence_name,
                shot_name,
            )
            readable_list.append(readable_shot)

        logger.info("Got shots %s." % readable_list)
        return readable_list
