# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import os
import sys
import threading

# by importing QT from sgtk rather than directly, we ensure that
# the code will be compatible with both PySide and PyQt.
from sgtk.platform.qt import QtCore, QtGui
from .ui.dialog import Ui_Dialog
# standard toolkit logger
logger = sgtk.platform.get_logger(__name__)


def show_dialog(app_instance):
    """
    Shows the main dialog window.
    """
    # in order to handle UIs seamlessly, each toolkit engine has methods for launching
    # different types of windows. By using these methods, your windows will be correctly
    # decorated and handled in a consistent fashion by the system.

    # we pass the dialog class to this method and leave the actual construction
    # to be carried out by toolkit.
    app_instance.engine.show_dialog("Show Project Versions", app_instance, AppDialog)

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
        self._app = sgtk.platform.current_bundle()
        self.sg = self._app.shotgun

        self.project_text = (str(self._app.context))
        self.project_code = self.project_text[-4:]

        self.sg_versions = self.get_version_info()
        self.sg_status_list = sorted(set([version["sg_status_list"] for version in self.sg_versions]))
        self.sg_status_list.insert(0, "All")

        # now load in the UI that was created in the UI designer
        self.setup_ui()
        self.connect_signals()

        # most of the useful accessors are available through the Application class instance
        # it is often handy to keep a reference to this. You can get it via the following method:
        self._app = sgtk.platform.current_bundle()

        # logging happens via a standard toolkit logger
        logger.info("Launching Starter Application...")

        # via the self._app handle we can for example access:
        # - The engine, via self._app.engine
        # - A Shotgun API instance, via self._app.shotgun
        # - An Sgtk API instance, via self._app.sgtk

        # lastly, set up our very basic UI

    def setup_ui(self):
        self.version_status_filter = QtGui.QComboBox(self)
        self.version_status_filter.setMinimumWidth(100)
        self.version_status_filter.setMaximumWidth(150)
        self.version_status_filter.addItems(self.sg_status_list)
        self.context_label = QtGui.QLabel(self.project_text)
        self.status_label = QtGui.QLabel("Filter by Status:")
        self.outerLayout = QtGui.QVBoxLayout()
        # Create a form layout for the label and line edit
        self.listLayout = QtGui.QFormLayout()
        # Create a layout for the checkboxes
        self.optionsLayout = QtGui.QHBoxLayout()
        # Add some checkboxes to the layout
        self.optionsLayout.addWidget(self.context_label)
        self.optionsLayout.addWidget(self.status_label)
        self.optionsLayout.addWidget(self.version_status_filter)
        # Nest the inner layouts into the outer layout
        self.outerLayout.addLayout(self.optionsLayout)
        # Set the window's main layout
        self.outerLayout.addLayout(self.listLayout)
        self.setLayout(self.outerLayout)
        self.update_version_rows()

    def connect_signals(self):
        self.version_status_filter.currentIndexChanged.connect(self.on_version_status_change)

    def get_version_info(self, status=None):
        # change filter based on status and project code from context
        filters = [
            ['project.Project.sg_project_code', 'is', self.project_code]
        ]
        if status:
            status_text = self.sg_status_list[status]
            if status != "All":
                filters.append(["sg_status_list", 'is', status_text])
        version_info = self.sg.find(
            'Version',
            filters=filters,
            fields=[
                "sg_status_list",
                "created_at",
                "code"
            ]
        )
        return version_info

    def update_version_rows(self):
        # First remove all objects in layout
        for i in reversed(range(self.listLayout.count())):
            self.listLayout.itemAt(i).widget().setParent(None)

        for version in self.sg_versions:
            # build out text to show
            comb_text = version["code"] + " - " + version["sg_status_list"]
            version_info_text = comb_text + " - " + version["created_at"].strftime("%b %d %Y")
            self.listLayout.addRow(QtGui.QLineEdit(version_info_text))

    def on_version_status_change(self):
        # get the status index and use it to collect the new versions
        status = self.version_status_filter.currentIndex()
        self.sg_versions = self.get_version_info(status)
        self.update_version_rows()
