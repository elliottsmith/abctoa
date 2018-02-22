# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/UI_ABCHierarchy.ui'
#
# Created: Thu Feb 22 13:15:28 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from milk.utils.v1_0.pyside.loader import QtCore, QtGui

class Ui_NAM(object):
    def setupUi(self, NAM):
        NAM.setObjectName("NAM")
        NAM.resize(1300, 730)
        NAM.setMinimumSize(QtCore.QSize(1300, 0))
        NAM.setBaseSize(QtCore.QSize(1280, 0))
        self.centralwidget = QtGui.QWidget(NAM)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.renderLayer = QtGui.QComboBox(self.centralwidget)
        self.renderLayer.setMinimumSize(QtCore.QSize(150, 0))
        self.renderLayer.setObjectName("renderLayer")
        self.gridLayout.addWidget(self.renderLayer, 0, 3, 1, 1)
        self.splitter = QtGui.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.hierarchyWidget = QtGui.QTreeWidget(self.splitter)
        self.hierarchyWidget.setMouseTracking(True)
        self.hierarchyWidget.setStyleSheet("QTreeWidget\n"
"\n"
"{\n"
"\n"
"border-style:solid;\n"
"    \n"
"border-width:1px;\n"
"    \n"
"border-color:#353535;\n"
"    \n"
"color:silver;\n"
"    \n"
"padding:5px;\n"
"    \n"
"border-top-right-radius : 5px;\n"
"    \n"
"border-top-left-radius : 5px;   \n"
"    \n"
"border-bottom-left-radius : 5px;\n"
"    \n"
"border-bottom-right-radius : 5px;   \n"
"}\n"
"\n"
"\n"
"\n"
"QTreeWidget::item:hover\n"
"\n"
"{\n"
"\n"
"border: none;\n"
"    \n"
"background: #000000;\n"
"    \n"
"border-radius: 3px;\n"
"}\n"
"\n"
"QTreeWidget::item:previously-selected\n"
"\n"
"\n"
"\n"
"{\n"
"\n"
"border: none;\n"
"}\n"
"\n"
"\n"
"\n"
"QTreeWidget::item:selected, QTreeWidget::item:previously-selected\n"
"\n"
"{\n"
"\n"
"border: none;\n"
"}")
        self.hierarchyWidget.setDragDropMode(QtGui.QAbstractItemView.DropOnly)
        self.hierarchyWidget.setAlternatingRowColors(True)
        self.hierarchyWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.hierarchyWidget.setRootIsDecorated(True)
        self.hierarchyWidget.setUniformRowHeights(False)
        self.hierarchyWidget.setColumnCount(2)
        self.hierarchyWidget.setObjectName("hierarchyWidget")
        self.hierarchyWidget.header().setVisible(True)
        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 4)
        self.wildCardButton = QtGui.QPushButton(self.centralwidget)
        self.wildCardButton.setMaximumSize(QtCore.QSize(200, 16777215))
        self.wildCardButton.setObjectName("wildCardButton")
        self.gridLayout.addWidget(self.wildCardButton, 2, 3, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.transform_check = QtGui.QCheckBox(self.centralwidget)
        self.transform_check.setChecked(True)
        self.transform_check.setObjectName("transform_check")
        self.horizontalLayout.addWidget(self.transform_check)
        self.shape_check = QtGui.QCheckBox(self.centralwidget)
        self.shape_check.setObjectName("shape_check")
        self.horizontalLayout.addWidget(self.shape_check)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.geoFilter = QtGui.QLineEdit(self.centralwidget)
        self.geoFilter.setMinimumSize(QtCore.QSize(350, 0))
        self.geoFilter.setObjectName("geoFilter")
        self.gridLayout.addWidget(self.geoFilter, 2, 2, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.overrideProps = QtGui.QCheckBox(self.centralwidget)
        self.overrideProps.setObjectName("overrideProps")
        self.horizontalLayout_2.addWidget(self.overrideProps)
        self.overrideShaders = QtGui.QCheckBox(self.centralwidget)
        self.overrideShaders.setObjectName("overrideShaders")
        self.horizontalLayout_2.addWidget(self.overrideShaders)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 2, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 2)
        NAM.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(NAM)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1300, 24))
        self.menubar.setObjectName("menubar")
        NAM.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(NAM)
        self.statusbar.setObjectName("statusbar")
        NAM.setStatusBar(self.statusbar)

        self.retranslateUi(NAM)
        QtCore.QMetaObject.connectSlotsByName(NAM)

    def retranslateUi(self, NAM):
        NAM.setWindowTitle(QtGui.QApplication.translate("NAM", "Alembic Cache Manager", None, QtGui.QApplication.UnicodeUTF8))
        self.hierarchyWidget.setSortingEnabled(False)
        self.hierarchyWidget.headerItem().setText(0, QtGui.QApplication.translate("NAM", "ABC Hierarchy", None, QtGui.QApplication.UnicodeUTF8))
        self.hierarchyWidget.headerItem().setText(1, QtGui.QApplication.translate("NAM", "shaders", None, QtGui.QApplication.UnicodeUTF8))
        self.wildCardButton.setText(QtGui.QApplication.translate("NAM", "Add WildCard Assignation", None, QtGui.QApplication.UnicodeUTF8))
        self.transform_check.setText(QtGui.QApplication.translate("NAM", "Xform", None, QtGui.QApplication.UnicodeUTF8))
        self.shape_check.setText(QtGui.QApplication.translate("NAM", "Shape", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("NAM", "Filter:", None, QtGui.QApplication.UnicodeUTF8))
        self.overrideProps.setText(QtGui.QApplication.translate("NAM", "Override all object properties", None, QtGui.QApplication.UnicodeUTF8))
        self.overrideShaders.setText(QtGui.QApplication.translate("NAM", "Override All Shaders", None, QtGui.QApplication.UnicodeUTF8))

