# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(521, 514)
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label1 = QtGui.QLabel(Dialog)
        self.label1.setObjectName("label1")

        self.verticalLayout.addWidget(self.label1)

        self.label2 = QtGui.QLabel(Dialog)
        self.label2.setObjectName("label2")

        self.verticalLayout.addWidget(self.label2)

        self.label3 = QtGui.QLabel(Dialog)
        self.label3.setObjectName("label3")

        self.verticalLayout.addWidget(self.label3)

        self.label4 = QtGui.QLabel(Dialog)
        self.label4.setObjectName("label4")

        self.verticalLayout.addWidget(self.label4)

        self.horizontalSpacer = QtGui.QSpacerItem(
            40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum
        )

        self.verticalLayout.addItem(self.horizontalSpacer)

        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.deliveryItemsLabel = QtGui.QLabel(Dialog)
        self.deliveryItemsLabel.setObjectName("deliveryItemsLabel")

        self.horizontalLayout_2.addWidget(self.deliveryItemsLabel)

        self.deliveryItems = QtGui.QListWidget(Dialog)
        self.deliveryItems.setObjectName("deliveryItems")

        self.horizontalLayout_2.addWidget(self.deliveryItems)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalSpacer_2 = QtGui.QSpacerItem(
            40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum
        )

        self.verticalLayout.addItem(self.horizontalSpacer_2)

        self.reload = QtGui.QPushButton(Dialog)
        self.reload.setObjectName("reload")

        self.verticalLayout.addWidget(self.reload)

        self.deliver = QtGui.QPushButton(Dialog)
        self.deliver.setObjectName("deliver")

        self.verticalLayout.addWidget(self.deliver)

        self.open_folder = QtGui.QPushButton(Dialog)
        self.open_folder.setObjectName("open_folder")

        self.verticalLayout.addWidget(self.open_folder)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)

        QtCore.QMetaObject.connectSlotsByName(Dialog)

    # def retranslateUi(self, Dialog):
    #     Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "The Current Sgtk Environment", None, QtGui.QApplication.UnicodeUTF8))
    #     self.context.setText(QtGui.QApplication.translate("Dialog", "Your Current Context: ", None, QtGui.QApplication.UnicodeUTF8))

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(
            QtCore.QCoreApplication.translate(
                "Dialog", "The Current Sgtk Environment", None
            )
        )
        self.label1.setText(
            QtCore.QCoreApplication.translate(
                "Dialog",
                '1. Set shots on ShotGrid to status "Ready for Delivery" ',
                None,
            )
        )
        self.label2.setText(
            QtCore.QCoreApplication.translate(
                "Dialog", "2. Optional: reload to see new items in list", None
            )
        )
        self.label3.setText(
            QtCore.QCoreApplication.translate(
                "Dialog",
                '3. Press the buton "Set ready for delivery" to move items to delivery folder',
                None,
            )
        )
        self.label4.setText(
            QtCore.QCoreApplication.translate(
                "Dialog",
                "4. Use open deliveries folder to open the delivery folder",
                None,
            )
        )
        self.deliveryItemsLabel.setText(
            QtCore.QCoreApplication.translate("Dialog", "Delivery items", None)
        )
        self.reload.setText(
            QtCore.QCoreApplication.translate("Dialog", "Reload", None)
        )
        self.deliver.setText(
            QtCore.QCoreApplication.translate(
                "Dialog", "Set ready for deliveries", None
            )
        )
        self.open_folder.setText(
            QtCore.QCoreApplication.translate(
                "Dialog", "Open deliveries folder", None
            )
        )

    # retranslateUi
