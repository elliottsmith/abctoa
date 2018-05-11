# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'maya/scripts/shaderManager/ui/UI_ABCHierarchy.ui'
#
# Created: Fri May 11 13:32:00 2018
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
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.renderLayer = QtGui.QComboBox(self.centralwidget)
        self.renderLayer.setMinimumSize(QtCore.QSize(150, 0))
        self.renderLayer.setObjectName("renderLayer")
        self.horizontalLayout_3.addWidget(self.renderLayer)
        self.layers_btn = QtGui.QPushButton(self.centralwidget)
        self.layers_btn.setMinimumSize(QtCore.QSize(20, 20))
        self.layers_btn.setMaximumSize(QtCore.QSize(20, 20))
        self.layers_btn.setText("")
        self.layers_btn.setObjectName("layers_btn")
        self.horizontalLayout_3.addWidget(self.layers_btn)
        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 5, 1, 1)
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
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.soloSelected = QtGui.QCheckBox(self.centralwidget)
        self.soloSelected.setObjectName("soloSelected")
        self.horizontalLayout_2.addWidget(self.soloSelected)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 3, 1, 1)
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
        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 6)
        self.wildCardButton = QtGui.QPushButton(self.centralwidget)
        self.wildCardButton.setMaximumSize(QtCore.QSize(200, 16777215))
        self.wildCardButton.setObjectName("wildCardButton")
        self.gridLayout.addWidget(self.wildCardButton, 2, 1, 1, 1)
        self.locatorsButton = QtGui.QPushButton(self.centralwidget)
        self.locatorsButton.setObjectName("locatorsButton")
        self.gridLayout.addWidget(self.locatorsButton, 2, 2, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 2)
        NAM.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(NAM)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1400, 25))
        self.menubar.setObjectName("menubar")
        NAM.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(NAM)
        self.statusbar.setObjectName("statusbar")
        NAM.setStatusBar(self.statusbar)

        self.retranslateUi(NAM)
        QtCore.QMetaObject.connectSlotsByName(NAM)

    def retranslateUi(self, NAM):
        NAM.setWindowTitle(QtGui.QApplication.translate("NAM", "Alembic Cache Manager", None, QtGui.QApplication.UnicodeUTF8))
        self.overrideProps.setText(QtGui.QApplication.translate("NAM", "Override properties", None, QtGui.QApplication.UnicodeUTF8))
        self.overrideShaders.setText(QtGui.QApplication.translate("NAM", "Override shaders", None, QtGui.QApplication.UnicodeUTF8))
        self.overrideDisps.setText(QtGui.QApplication.translate("NAM", "Override displacements", None, QtGui.QApplication.UnicodeUTF8))
        self.soloSelected.setText(QtGui.QApplication.translate("NAM", "Solo Selected", None, QtGui.QApplication.UnicodeUTF8))
        self.hierarchyWidget.setSortingEnabled(False)
        self.hierarchyWidget.headerItem().setText(0, QtGui.QApplication.translate("NAM", "ABC Hierarchy", None, QtGui.QApplication.UnicodeUTF8))
        self.hierarchyWidget.headerItem().setText(1, QtGui.QApplication.translate("NAM", "shaders", None, QtGui.QApplication.UnicodeUTF8))
        self.hierarchyWidget.headerItem().setText(2, QtGui.QApplication.translate("NAM", "displacement", None, QtGui.QApplication.UnicodeUTF8))
        self.wildCardButton.setText(QtGui.QApplication.translate("NAM", "Add WildCard Assignation", None, QtGui.QApplication.UnicodeUTF8))
        self.locatorsButton.setText(QtGui.QApplication.translate("NAM", "Import All Locators", None, QtGui.QApplication.UnicodeUTF8))

