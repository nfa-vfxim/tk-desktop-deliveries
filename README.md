[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# ShotGrid deliveries app
This app will get all shots with the "Ready for Delivery" status, and copy the publishes to the delivery folder with the correct naming convention. Currently used at the Netherlands Film Academy.

## User interface
![tk-desktop-deliveries](./resources/tk-desktop-deliveries.png)

## Requirements
* This app will need a sg_projectcode field on the project in ShotGrid

## Settings
* `delivery_sequence`: template to move the file sequence to
* `delivery_folder`: template to the delivery folder
* `default_root`: string for the root project, defaults to `primary`.
* `delivery_status`: string with the shot shortcode status for shots to be delivered. Defaults to `rfd` for `Ready for Delivery`.
* `delivered_status`: string with the shot shortcode status for shots that are delivered. Defaults to `fin` for `Final`.
