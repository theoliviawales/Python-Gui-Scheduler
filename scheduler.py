"""
Richard Wales, October 2016

The Remastered, QT Gui version of the famed Python Scheduler. The old code
that ran the scheduler through the terminal has been migrated and slightly
altered to work with a QT interface. Much of the code could be optimized for
the fact that the GUI is now being used, but simply injecting the old code 
base was an easy beginning step :)
"""

import sys
import qdarkstyle
from PySide.QtCore import Qt
from PySide.QtGui import QMainWindow, QApplication, QLabel, QStyleFactory, QTableWidgetItem
from schedui import Ui_Schedule 

class Course(object):
    """
    This class holds day and time information for a course such that it can be 
    easily compared to other courses to see if two courses conflict in times
    """
    
    def __init__(self, times, name):
        """
        Creates a new course with the given times and name

        Args:
            times: a dict containing days (key) mapping to times (values)
            name: a str containing the course name
        """
        self.times = times
        self.name = name

        # Maybe make this a class variable?
        self.numToDay = {1:'M', 2:'T', 3:'W', 4:'R', 5:'F'}

    def printCourse(self):
        """
        Nothing to see here, just a nice debugging tool :)
        """
        print self.name
        for day, time in self.times.items():
            print self.numToDay[day], time
        print

    def valid(self, otherCourse):
        """
        Compares date/times for two courses to see if they conflict

        Args:
            otherCourse: another course object to compare to
        
        Returns:
            boolean of whether the classes can be placed together or not
        """
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
    """
    Master GUI class. Inherits from a class generated from Pyside-uic that
    contains code for the components made in QtDesigner. The button signals
    are connected to functions to add/remove/generate items in the schedule
    """

    def __init__(self):
        """
        Sets up the GUI and connects button signals
        
        Also intializes a few sets to assist in class removal from the 
        list widgets
        """
        super(Scheduler, self).__init__()
        self.setupUi(self)

        self.addToScheduleBtn.clicked.connect(self.newCourse)
        self.addClassBtn.clicked.connect(self.addClassToList)
        self.removeBtn.clicked.connect(self.removeFromList)
        self.removeFromSchedBtn.clicked.connect(self.removeFromSched)
        self.generateBtn.clicked.connect(self.generate)
        self.generatedWeeksCombo.currentIndexChanged.connect(self.displayTable)

        self.dayButtons = [self.mDay, self.tDay, self.wDay, self.rDay, self.fDay]
        self.classInList = set()
        self.classInSched = set()
        self.tables = []

        self.show()

    def removeFromSched(self):
        """
        Removes the current item selected in the Schedule
        list widget. Also removes it from the classInSched set
        """
        name = self.scheduleList.currentItem().text()
        self.scheduleList.takeItem(self.scheduleList.currentRow())
        self.classInSched.remove(name)

    def removeFromList(self):
        """
        Removes the currently selected class from the class list
        widget, as well as the set corresponding to the class list.
        The set is used to reconstruct the new combobox items. The 
        set was necessary as normally you would need the combobox index
        of the removed item to actually remove it from the combobox. Clearing
        and recreating it is simpler. A dict mapping names to indices could have
        been used instead, and may be a better approach for larger use-cases
        """
        name = self.classList.currentItem().text() 
        self.classList.takeItem(self.classList.currentRow())
        self.classInList.remove(name)

        self.classSelector.clear()
        self.classSelector.addItems(list(self.classInList))

    def addClassToList(self):
        """
        Adds the class name entered into the textfield into the class list
        widget, as well as the set and combobox. 
        """
        name = self.courseNameText.toPlainText()
        self.classList.addItem(name)
        self.classSelector.addItem(name)
        self.classInList.add(name)
        self.courseNameText.clear()

    def newCourse(self):
        """
        Takes the inputted course information and adds the new course to the 
        schedule list widget, formatted in the format matching the previous
        scheduler's so that the parsing does not need to be rewritten... yet...
        """

        # This is used sort of like a java StringBuilder so that new Strings are
        # not constantly being allocated for, but being a dynamic array, the memory
        # being wasted may undo the good it is doing
        courseText = []

        if self.classSelector.currentText() == '':
            return

        courseText.append(self.classSelector.currentText())
        
        # This bool ensures that a course is not added unless it has days specified
        noneChecked = True
        for button in self.dayButtons:
            if button.isChecked():
                noneChecked = False

                # Abuse the fact that the buttons are named with the first letter
                # being the day they represent :)
                day = button.objectName()[0].upper()
                startTime = self.startTime.time()
                endTime = self.endTime.time()
                formatTimes = str(startTime.hour()) + ':' + str(startTime.minute()) + \
                        '-' + str(endTime.hour()) + ':' + str(endTime.minute())
                courseText.append(day + formatTimes)

                button.setCheckState(Qt.Unchecked)

        if noneChecked:
            return 

        formattedClass = ' '.join(courseText)
        self.scheduleList.addItem(formattedClass)
        self.classInSched.add(formattedClass)

    def importClasses(self, classes):
        """
        Takes a list of formatted class strings and turns them into 'Course' objects. Because
        the way the GUI is now done, this function could be avoided by having the Course objects
        be created whenever 'newCourse' is called, however for now, it was easier to migrate the
        old Terminal scheduler code to work like this, being injected into the GUI code. 

        Args:
            classes[]: list of strings. Course code, then days and times space separated
            ex: COP3502 M9:30-10:20 W9:30-10:20
            The format comes from the schedule list widget, done by the newCourse method 

        Returns:
            A list of Course objects that have the class information from classes
        """
        courses = []
        weekdayDict = {'M':1, 'T':2, 'W':3, 'R':4, 'F':5}

        for course in classes:
            splitStr = course.split()
            name = splitStr[0]
            times = {}

            # The (-1) accounts for the first spot being the class name in the list
            for i in xrange(len(splitStr)-1):
                courseTime = splitStr[1 + i]
                weekday = weekdayDict[courseTime[0]]

                # Parse the time by looking for ':' to denote splitting hours and minutes
                # as well as the '-' to split start and end times. Could using .split() have
                # been more helpful? Hmm...
                startTime = int(courseTime[1:courseTime.find(':')]) * 100 \
                + int(courseTime[courseTime.find(':') + 1:courseTime.find('-')])

                endTime = int(courseTime[courseTime.find('-')+1:courseTime.find(':', 5)]) * 100 + \
                int(courseTime[courseTime.find(':', 5) + 1:])

                times[weekday] = (startTime, endTime)

            newCourse = Course(times, name)
            courses.append(newCourse)
        
        return courses

    def generate(self):
        """
        Where the magic happens. importClasses turns the list widget containing the 
        classes and times into Course objects. A backtracking algorithm finds every 
        possible scheduling arrangement, and then sends the data to a table in the
        'Generated' tab
        """
        courses = self.importClasses(list(self.classInSched))
        weeks = []

        self.findMatches(courses, 0, [], len(self.classInList), [], weeks)
        
        self.generatedWeeksCombo.clear()
        self.generatedTable.clear()
        self.generatedWeeksCombo.addItems([str(n) for n in range(1, len(weeks)+1)])
        
        self.tables = weeks
        self.displayTable()

    def displayTable(self):
        """
        Depending on what schedule is being viewed (as denoted by the combobox),
        the table widget is populated with data from the tables list
        """
        if not self.tables:
            return
        
        # This second clear is used so that a table is cleared upon changing the
        # combobox index, as well as if a new schedule is generated
        self.generatedTable.clear()

        # The table index where the data will be fetched from the tables list
        table = self.tables[self.generatedWeeksCombo.currentIndex()]

        self.generatedTable.setRowCount(len(table))
        self.generatedTable.setColumnCount(len(table[0]))

        for i in xrange(len(table)):
            for j in xrange(len(table[i])):
                if table[i][j]:
                    self.generatedTable.setItem(i, j, QTableWidgetItem(str(table[i][j])))
                    self.generatedTable.resizeRowToContents(i)

    def findMatches(self, courses, index, chosenCourses, numCourses, memo, weeks):
        """
        A backtracking algorithm that builds every valid schedule possible, given the
        courses from the courses list.

        Args:
            courses: A list of Course objects corresponding to the possible courses
            index: The current index in courses that is to be possibly chosen
            chosenCourses: A list of courses that have been selected to build a schedule
            numCourses: The number of courses necessary to be added to chosenCourses
            
            TODO (Rwales): Change memo to a set and make Course objects comparable
            memo: A list corresponding to the courses already seen. 
            
            weeks: The list that will contain all of the valid weekly schedules
        """
        if len(chosenCourses) == numCourses and chosenCourses not in memo:
            memo.append(list(chosenCourses))
            weeks.append(self.formatTable(chosenCourses))

        # If we have reached the end of our list of courses, but there are not 
        # enough chosen courses to build a complete schedule, return 
        if index == len(courses):
            return
        
        # Compare a candidate course to every course chosen so far to check validity
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
        """
        Turn a list of Course objects into a beautiful 2D list that can be easily
        translated into a QtTableWidget for display

        Args:
            courses: A list of chosen Course objects from the backtracking algorithm

        Returns:
            A 2D list containing the formatted table information
        """
        
        # Sort the times by the start so that we can greedily choose what times are
        # placed first in the table. Greedy algorithms, hooray for CS!
        startTimes = sorted([course.times.values()[0][0] for course in courses])

        timeToIndex = {}
        tableList = []

        for i in xrange(len(courses) + 1):
            tableList.append([[], [], [], [], []])
        
        # This is the top header of the table.
        tableList[0][0] = 'Mon'
        tableList[0][1] = 'Tues'
        tableList[0][2] = 'Wed'
        tableList[0][3] = 'Thur'
        tableList[0][4] = 'Fri'

        # This is the greedy part. Put the earliest times at the topmost rows
        for x in xrange(len(courses)):
            timeToIndex[startTimes[x]] = x
        
        for course in courses:
            days = course.times.keys()
            
            for day in days:
                # Converting the times from easily comparable integer, military times, to normal 12HR times
                courseString = course.name + '\n' + "%2d:%02d -%2d:%02d" %(course.times[day][0]/100 - \
                12*(0 if course.times[day][0]/100 <= 12 else 1), course.times[day][0]%100, course.times[day][1]/100 - \
                12*(0 if course.times[day][1]/100 <= 12 else 1), course.times[day][1]%100)  
                tableList[timeToIndex[course.times[day][0]] + 1][day-1] = courseString
        
        return tableList

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    s = Scheduler()
    ret = app.exec_()
    sys.exit(ret)

        