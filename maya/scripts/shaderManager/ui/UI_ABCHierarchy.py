# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'shaderManager/ui/UI_ABCHierarchy.ui'
#
# Created: Thu Mar  1 17:45:25 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from milk.utils.v1_0.pyside.loader import QtCore, QtGui

class Ui_NAM(object):
    def setupUi(self, NAM):
        NAM.setObjectName("NAM")
        NAM.resize(1400, 730)
        NAM.setMinimumSize(QtCore.QSize(1400, 0))
        NAM.setBaseSize(QtCore.QSize(1280, 0))
        self.centralwidget = QtGui.QWidget(NAM)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.wildCardButton = QtGui.QPushButton(self.centralwidget)
        self.wildCardButton.setMaximumSize(QtCore.QSize(200, 16777215))
        self.wildCardButton.setObjectName("wildCardButton")
        self.gridLayout.addWidget(self.wildCardButton, 2, 4, 1, 1)
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
        self.geoFilter.setMinimumSize(QtCore.QSize(250, 0))
        self.geoFilter.setObjectName("geoFilter")
        self.gridLayout.addWidget(self.geoFilter, 2, 2, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.renderLayer = QtGui.QComboBox(self.centralwidget)
        self.renderLayer.setMinimumSize(QtCore.QSize(150, 0))
        self.renderLayer.setObjectName("renderLayer")
        self.horizontalLayout_3.addWidget(self.renderLayer)
        self.layerUtilities = QtGui.QPushButton(self.centralwidget)
        self.layerUtilities.setMinimumSize(QtCore.QSize(32, 32))
        self.layerUtilities.setMaximumSize(QtCore.QSize(32, 32))
        self.layerUtilities.setText("")
        self.layerUtilities.setObjectName("layerUtilities")
        self.horizontalLayout_3.addWidget(self.layerUtilities)
        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 4, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.overrideProps = QtGui.QCheckBox(self.centralwidget)
        self.overrideProps.setObjectName("overrideProps")
        self.horizontalLayout_2.addWidget(self.overrideProps)
        self.overrideShaders = QtGui.QCheckBox(self.centralwidget)
        self.overrideShaders.setObjectName("overrideShaders")
        self.horizontalLayout_2.addWidget(self.overrideShaders)
        self.overrideDisps = QtGui.QCheckBox(self.centralwidget)
        self.overrideDisps.setObjectName("overrideDisps")
        self.horizontalLayout_2.addWidget(self.overrideDisps)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 2, 1, 1)
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
        self.hierarchyWidget.setColumnCount(3)
        self.hierarchyWidget.setObjectName("hierarchyWidget")
        self.hierarchyWidget.header().setVisible(True)
        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 5)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 2)
        NAM.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(NAM)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1400, 24))
        self.menubar.setObjectName("menubar")
        NAM.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(NAM)
        self.statusbar.setObjectName("statusbar")
        NAM.setStatusBar(self.statusbar)

        self.retranslateUi(NAM)
        QtCore.QMetaObject.connectSlotsByName(NAM)

    def retranslateUi(self, NAM):
        NAM.setWindowTitle(QtGui.QApplication.translate("NAM", "Alembic Cache Manager", None, QtGui.QApplication.UnicodeUTF8))
        self.wildCardButton.setText(QtGui.QApplication.translate("NAM", "Add WildCard Assignation", None, QtGui.QApplication.UnicodeUTF8))
        self.transform_check.setText(QtGui.QApplication.translate("NAM", "Xform", None, QtGui.QApplication.UnicodeUTF8))
        self.shape_check.setText(QtGui.QApplication.translate("NAM", "Shape", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("NAM", "Select:", None, QtGui.QApplication.UnicodeUTF8))
        self.overrideProps.setText(QtGui.QApplication.translate("NAM", "Override properties", None, QtGui.QApplication.UnicodeUTF8))
        self.overrideShaders.setText(QtGui.QApplication.translate("NAM", "Override shaders", None, QtGui.QApplication.UnicodeUTF8))
        self.overrideDisps.setText(QtGui.QApplication.translate("NAM", "Override displacements", None, QtGui.QApplication.UnicodeUTF8))
        self.hierarchyWidget.setSortingEnabled(False)
        self.hierarchyWidget.headerItem().setText(0, QtGui.QApplication.translate("NAM", "ABC Hierarchy", None, QtGui.QApplication.UnicodeUTF8))
        self.hierarchyWidget.headerItem().setText(1, QtGui.QApplication.translate("NAM", "shaders", None, QtGui.QApplication.UnicodeUTF8))
        self.hierarchyWidget.headerItem().setText(2, QtGui.QApplication.translate("NAM", "displacement", None, QtGui.QApplication.UnicodeUTF8))

