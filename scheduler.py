"""
The Remastered, QT Gui version of the famed Python Scheduler
"""

import sys

# Unnecessary import to PySide.QtCore 
from PySide.QtGui import QMainWindow, QApplication, QLabel, QStyleFactory
from schedui import Ui_Schedule 

class Scheduler(QMainWindow, Ui_Schedule):
    def __init__(self):
        super(Scheduler, self).__init__()
        self.setupUi(self)
        self.addToScheduleBtn.clicked.connect(self.newCourse)
        self.addClassBtn.clicked.connect(self.addClassToList)
        self.removeBtn.clicked.connect(self.removeFromList)
        self.classInList = set()
        self.show()

    def removeFromList(self):
        name = self.classList.currentItem().text() 
        self.classList.takeItem(self.classList.currentRow())
        self.classSelector.clear()
        self.classInList.remove(name)
        self.classSelector.addItems(list(self.classInList))

    def addClassToList(self):
        name = self.courseNameText.toPlainText()
        self.classList.addItem(name)
        self.classSelector.addItem(name)
        self.classInList.add(name)

    def newCourse(self):
        self.scheduleList.insertItem(0, self.classSelector.currentText())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Plastique'))
    s = Scheduler()
    ret = app.exec_()
    sys.exit(ret)

        