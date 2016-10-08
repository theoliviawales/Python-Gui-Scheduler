"""
The Remastered, QT Gui version of the famed Python Scheduler
"""

import sys

# Unnecessary import to PySide.QtCore 
from PySide.QtGui import QMainWindow, QApplication, QLabel, QStyleFactory, QTableWidgetItem
from schedui import Ui_Schedule 

class Course(object):
    def __init__(self, times, name):
        self.times = times
        self.name = name
        self.numToDay = {1:'M', 2:'T', 3:'W', 4:'R', 5:'F'}

    def printCourse(self):
        print self.name
        for day, time in self.times.items():
            print self.numToDay[day], time
        print

    def valid(self, otherCourse):
        if self.name == otherCourse.name:
            return False

        for day in self.times:
            start = self.times[day][0]
            end = self.times[day][1]
            for otherDay in otherCourse.times:
                oStart = otherCourse.times[otherDay][0]
                oEnd = otherCourse.times[otherDay][1]
                if day == otherDay:
                    if not (start > oEnd or oStart > end):
                        return False
        return True

class Scheduler(QMainWindow, Ui_Schedule):
    def __init__(self):
        super(Scheduler, self).__init__()
        self.setupUi(self)
        self.addToScheduleBtn.clicked.connect(self.newCourse)
        self.addClassBtn.clicked.connect(self.addClassToList)
        self.removeBtn.clicked.connect(self.removeFromList)
        self.removeFromSchedBtn.clicked.connect(self.removeFromSched)
        self.generateBtn.clicked.connect(self.generate)
        self.dayButtons = [self.mDay, self.tDay, self.wDay, self.rDay, self.fDay]
        self.generatedWeeksCombo.currentIndexChanged.connect(self.displayTable)
        self.classInList = set()
        self.classInSched = set()
        self.tables = []

        self.show()

    def removeFromSched(self):
        name = self.scheduleList.currentItem().text()
        self.scheduleList.takeItem(self.scheduleList.currentRow())
        self.classInSched.remove(name)

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
        # self.scheduleList.insertItem(0, self.classSelector.currentText())
        courseText = []

        if self.classSelector.currentText() == '':
            return

        courseText.append(self.classSelector.currentText())
        
        noneChecked = True
        for button in self.dayButtons:
            if button.isChecked():
                noneChecked = False
                day = button.objectName()[0].upper()
                startTime = self.startTime.time()
                endTime = self.endTime.time()
                formatTimes = str(startTime.hour()) + ':' + str(startTime.minute()) + \
                        '-' + str(endTime.hour()) + ':' + str(endTime.minute())
                courseText.append(day + formatTimes)
        if noneChecked:
            return 
        formattedClass = ' '.join(courseText)
        self.scheduleList.addItem(' '.join(courseText))
        self.classInSched.add(formattedClass)

    def importClasses(self, classes):
        """
        classes[]: list of strings. Course code, then days and times space separated
        ex: COP3502 M9:30-10:20 W9:30-10:20 
        """
        courses = []
        weekdayDict = {'M':1, 'T':2, 'W':3, 'R':4, 'F':5}
        for course in classes:
            splitStr = course.split()
            name = splitStr[0]
            times = {}

            for i in xrange((len(splitStr)-1)/2 + 1):
                courseTime = splitStr[1 + i]
                weekday = weekdayDict[courseTime[0]]

                startTime = int(courseTime[1:courseTime.find(':')]) * 100 \
                + int(courseTime[courseTime.find(':') + 1:courseTime.find('-')])
                endTime = int(courseTime[courseTime.find('-')+1:courseTime.find(':', 5)]) * 100 + \
                int(courseTime[courseTime.find(':', 5) + 1:])
                times[weekday] = (startTime, endTime)
            newCourse = Course(times, name)
            courses.append(newCourse)
        return courses

    def generate(self):
        courses = self.importClasses(list(self.classInSched))
        weeks = []
        self.findMatches(courses, 0, [], len(self.classInList), [], weeks)
        self.generatedWeeksCombo.clear()
        self.generatedWeeksCombo.addItems([str(n) for n in range(1, len(weeks)+1)])
        self.generatedTable.clear()
        self.tables = weeks
        self.displayTable()

    def displayTable(self):
        if not self.tables:
            return
        
        self.generatedTable.clear()
        table = self.tables[self.generatedWeeksCombo.currentIndex()]
        self.generatedTable.setRowCount(len(table))
        self.generatedTable.setColumnCount(len(table[0]))

        for i in xrange(len(table)):
            for j in xrange(len(table[i])):
                if table[i][j]:
                    self.generatedTable.setItem(i, j, QTableWidgetItem(str(table[i][j])))
                    self.generatedTable.resizeRowToContents(i)


    def findMatches(self, courses, index, chosenCourses, numCourses, memo, weeks):
        if len(chosenCourses) == numCourses and chosenCourses not in memo:
            memo.append(list(chosenCourses))
            weeks.append(self.formatTable(chosenCourses))

        if index == len(courses):
            return
        
        valid = True
        for course in chosenCourses:
            if not course.valid(courses[index]):
                valid = False
        self.findMatches(courses, index + 1, chosenCourses, numCourses, memo, weeks)
        
        if valid:
            chosenCourses.append(courses[index])
            self.findMatches(courses, index + 1, chosenCourses, numCourses, memo, weeks)
            chosenCourses.remove(courses[index])        

    def formatTable(self, courses):
        startTimes = sorted([course.times.values()[0][0] for course in courses])
        timeToIndex = {}
        tableList = []

        for i in xrange(len(courses) + 1):
            tableList.append([[], [], [], [], []])

        tableList[0][0] = 'Mon'
        tableList[0][1] = 'Tues'
        tableList[0][2] = 'Wed'
        tableList[0][3] = 'Thur'
        tableList[0][4] = 'Fri'

        for x in xrange(len(courses)):
            timeToIndex[startTimes[x]] = x
        
        for course in courses:
            days = course.times.keys()
            
            for day in days:
                courseString = course.name + '\n' + "%2d:%02d -%2d:%02d" %(course.times[day][0]/100 - \
                12*(0 if course.times[day][0]/100 <= 12 else 1), course.times[day][0]%100, course.times[day][1]/100 - \
                12*(0 if course.times[day][1]/100 <= 12 else 1), course.times[day][1]%100)  
                tableList[timeToIndex[course.times[day][0]] + 1][day-1] = courseString
        
        return tableList
        

    def drawWeek(self, numClasses, courses):
        # Initializes NxN array of empty strings
        table = ["" for x in xrange((numClasses*2)**2)]
        startTimes = sorted([course.times.values()[0][0] for course in courses])
        timeToIndex = {}
        for x in xrange(numClasses):
            timeToIndex[startTimes[x]] = x

        for course in courses:
            days = course.times.keys()
            for day in days:
                listIndex = (day-1) + numClasses * timeToIndex[course.times[day][0]]*2
                table[listIndex] = course.name
                table[listIndex+numClasses] = "%2d:%02d -%2d:%02d" %(course.times[day][0]/100 - \
                12*(0 if course.times[day][0]/100 <= 12 else 1), course.times[day][0]%100, course.times[day][1]/100 - \
                12*(0 if course.times[day][1]/100 <= 12 else 1), course.times[day][1]%100) 
        cal = """+------------------+-------------------+------------------+------------------+------------------+\n"""
        cal += """|{:^18}| {:^18}|{:^18}|{:^18}|{:^18}|\n""".format("Mon", "Tues", "Wed", "Thur", "Fri")
        cal += """+------------------+-------------------+------------------+------------------+------------------+\n""" + \
    """|{:^18}| {:^18}|{:^18}|{:^18}|{:^18}|
|{:^18}| {:^18}|{:^18}|{:^18}|{:^18}|
+------------------+-------------------+------------------+------------------+------------------+

""" * numClasses
        return cal.format(*table)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    #app.setStyle(QStyleFactory.create('Plastique'))
    s = Scheduler()
    ret = app.exec_()
    sys.exit(ret)

        