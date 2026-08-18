"""Command to show the RobotCAD version (read from package.xml)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import FreeCAD as fc
import FreeCADGui as fcgui

try:
    from PySide import QtWidgets
except ImportError:
    from PySide6 import QtWidgets

from ..gui_utils import tr
from ..wb_constants import MOD_PATH


def _get_package_xml_value(tag: str) -> str:
    """Read a top-level element value from the addon's package.xml.

    Returns the element text, or an empty string if it cannot be determined.
    """
    package_xml = MOD_PATH / 'package.xml'
    if not package_xml.exists():
        return ''
    try:
        tree = ET.parse(str(package_xml))
        root = tree.getroot()
        # package.xml may declare a default namespace, so search all elements
        # regardless of namespace.
        for elem in root.iter():
            if elem.tag.rsplit('}', 1)[-1] == tag:
                if elem.text:
                    return elem.text.strip()
    except ET.ParseError:
        pass
    return ''


def get_robotcad_version() -> str:
    """Read the RobotCAD version from the addon's package.xml."""
    return _get_package_xml_value('version')


def get_robotcad_release_date() -> str:
    """Read the RobotCAD release date from the addon's package.xml."""
    return _get_package_xml_value('date')


class _AboutCommand:
    """The command definition to show the RobotCAD version."""

    def GetResources(self):
        return {
            'Pixmap': 'about_robotcad.svg',
            'MenuText': tr('About RobotCAD'),
            'Accel': 'W, A',
            'ToolTip': tr('Show RobotCAD version information'),
        }

    def IsActive(self):
        return True

    def Activated(self):
        version = get_robotcad_version() or tr('unknown')
        release_date = get_robotcad_release_date() or tr('unknown')
        message = (
            tr('RobotCAD version: {}').format(version) + '\n' +
            tr('Release date: {}').format(release_date)
        )

        QtWidgets.QMessageBox.information(
            None,
            tr('About RobotCAD'),
            message,
        )


fcgui.addCommand('AboutRobotCAD', _AboutCommand())
