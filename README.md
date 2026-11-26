[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# ShotGrid deliveries app
This app lists all shots in the project, grouped per sequence with checkboxes. The latest version of every ticked shot is linked to the delivery folder with the correct naming convention. Currently used at the Netherlands Film Academy.

## User interface
![delivery_export](https://github.com/nfa-vfxim/tk-desktop-deliveries/assets/63094424/46c7fbab-84c8-401e-8627-eb25b315b313)


## Requirements
* This app will need a sg_projectcode field on the project in ShotGrid

## Settings
* `delivery_sequence`: template to move the file sequence to
* `delivery_folder`: template to the delivery folder
* `default_root`: string for the root project, defaults to `primary`.
* `preselect_status`: shots with this status are ticked by default. Defaults to `rfd`. All shots are always listed.
* `set_delivered_status`: if true, set the shot status to `delivered_status` after delivery. Defaults to `false` (statuses are never changed).
* `delivered_status`: status used when `set_delivered_status` is true. Defaults to `fin`.
