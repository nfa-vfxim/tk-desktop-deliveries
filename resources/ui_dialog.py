# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.3.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QListView, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)
import resources_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(521, 514)
        self.horizontalLayout = QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label1 = QLabel(Dialog)
        self.label1.setObjectName(u"label1")

        self.verticalLayout.addWidget(self.label1)

        self.label2 = QLabel(Dialog)
        self.label2.setObjectName(u"label2")

        self.verticalLayout.addWidget(self.label2)

        self.label3 = QLabel(Dialog)
        self.label3.setObjectName(u"label3")

        self.verticalLayout.addWidget(self.label3)

        self.label4 = QLabel(Dialog)
        self.label4.setObjectName(u"label4")

        self.verticalLayout.addWidget(self.label4)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.verticalLayout.addItem(self.horizontalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.deliveryItemsLabel = QLabel(Dialog)
        self.deliveryItemsLabel.setObjectName(u"deliveryItemsLabel")

        self.horizontalLayout_2.addWidget(self.deliveryItemsLabel)

        self.deliveryItems = QListView(Dialog)
        self.deliveryItems.setObjectName(u"deliveryItems")

        self.horizontalLayout_2.addWidget(self.deliveryItems)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.verticalLayout.addItem(self.horizontalSpacer_2)

        self.pushButton_3 = QPushButton(Dialog)
        self.pushButton_3.setObjectName(u"pushButton_3")

        self.verticalLayout.addWidget(self.pushButton_3)

        self.pushButton = QPushButton(Dialog)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(Dialog)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.verticalLayout.addWidget(self.pushButton_2)


        self.horizontalLayout.addLayout(self.verticalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"The Current Sgtk Environment", None))
        self.label1.setText(QCoreApplication.translate("Dialog", u"1. Set shots on ShotGrid to status \"Ready for Delivery\" ", None))
        self.label2.setText(QCoreApplication.translate("Dialog", u"2. Optional: reload to see new items in list", None))
        self.label3.setText(QCoreApplication.translate("Dialog", u"3. Press the buton \"Set ready for delivery\" to move items to delivery folder", None))
        self.label4.setText(QCoreApplication.translate("Dialog", u"4. Use open deliveries folder to open the delivery folder", None))
        self.deliveryItemsLabel.setText(QCoreApplication.translate("Dialog", u"Delivery items", None))
        self.pushButton_3.setText(QCoreApplication.translate("Dialog", u"Reload", None))
        self.pushButton.setText(QCoreApplication.translate("Dialog", u"Set ready for deliveries", None))
        self.pushButton_2.setText(QCoreApplication.translate("Dialog", u"Open deliveries folder", None))
    # retranslateUi

