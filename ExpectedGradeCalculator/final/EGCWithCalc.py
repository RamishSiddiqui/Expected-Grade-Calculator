from time import sleep
from os import getcwd, rename, listdir, remove, path, mkdir
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from pdftotext import PDF
from math import ceil

degree_name = ""
Directory = path.join(getcwd(), "Report")


def MakeFolder():
    try:
        mkdir(Directory)
    except OSError:
        print("Creation of the directory", Directory, " failed")
    else:
        print("Successfully created the directory", Directory)


def SetDegree(RegisterationNumber):
    return RegisterationNumber[5:7]


def TrucateString(marks):
    # ------------- removing all : and spaces from the string
    marks = [line.strip().split("\n") for line in marks]  # make string list
    marks = [item for sublist in marks for item in
             sublist]  # above line make list of list thereefore converting it back to the list
    for mytext, i in zip(marks, range(len(marks))):
        mytext = mytext.replace(':', '')  # replacing all : into spaces
        marks[i] = ' '.join([x for x in mytext.split(' ') if len(x) > 0])  # removing all extra spaces in the string.
    return marks


def FileWriting(marks):
    # -------------this function help us in converting the string in the datatype that we want and remove all unnecessary data
    file = open('output.txt', 'w')
    for i in marks:
        if i.find("Total") == -1:
            indexAM = i.find("AM")
            indexPM = i.find("PM")
            if indexAM != -1:
                i = i[indexAM + 3:len(i)]
            if indexPM != -1:
                i = i[indexPM + 3:len(i)]
            file.write(i)
            file.write("\n")


class Course:
    Name = "0"
    ID = "0"
    Assets = {}  # For Marks Name:(Total, Obtained)
    WeightagesAndBestOf = {}  # Name:(Best Of, Weightage)
    Absolutes = {}  # Name:(Obtained Absolute, Weightage)
    Grade = "0"
    Header = []
    isEmpty = False
    percentage = 0.0
    Semester = "0"

    # ---------------PRIVATE FUNCTIONS
    def __RemoveHeaderAndFooter(self, pdf):
        marks = []
        header = []
        for page in pdf:
            # ------------- this is to remove header
            index = page.rindex(degree_name)  # find index of the BS(last word in header)
            header = page[:index + 3]
            page = page[index + 3:len(page)] if index != -1 else page  # slice the string uptil BS

            # ------------- this is to remove footer
            index = page.find("Page")  # find the index of the page(first word in footer)
            page = page[0:index] if index != -1 else page  # slice the string
            marks.append(page)  # converting PDF type object in list of string

        self.Header = list(header.split("\n"))
        return marks

    def __Refresh(self):
        self.Name = "0"
        self.ID = "0"
        self.Assets = {}  # For Marks Name:(Total, Obtained)
        self.WeightagesAndBestOf = {}  # Name:(Best Of, Weightage)
        self.Absolutes = {}  # Name:(Obtained Absolute, Weightage)
        self.Grade = "0"
        self.Header = []
        self.percentage = 0.0
        self.Empty = False
        self.Semester = "0"

    def __CalculateAbsolute(self, field):  # field: quiz, assignment etc
        # ------------- Calculating the absolute marks in the given field
        marks = self.Assets[field]
        Best_of = self.WeightagesAndBestOf[field]
        if len(marks) == 1 and marks[0][0] == 0:
            print("==> " + field + " marks has not been uploaded!!!!")
            return 0
        else:
            marks = [nonZeroObtain for nonZeroObtain in marks if nonZeroObtain[1] != 0] + \
                    [ZeroObtain for ZeroObtain in marks if ZeroObtain[1] == 0]
            marks.sort(key=lambda x: x[1] / x[0] if x[1] != 0 else 0, reverse=True)
            if Best_of[0] != 0:
                marks = marks[:Best_of[0]]
            total, obtain = sum(item[0] for item in marks), sum(item[1] for item in marks)
            return (obtain / total) * Best_of[1]

    def __FileReading(self):
        # ------------- read data from the file
        count = 0
        key = ""
        values = []
        with open("output.txt") as file:
            for Lines in file:
                index = Lines.find("Title")  # find the word tile after title there is a key(Assignment, Quizess etc)
                if index != -1:
                    count += 1
                    if count >= 2:
                        self.Assets[key] = values  # Set values in Asset
                        key = ""
                        values = []
                    key = Lines[index + len("Title") + 1:len(
                        Lines) - 1]  # +1 means there is a space in the string after word 'title' soo we slice it
                    # -1 means there is a \n in the end of string soo we slice it
                else:
                    values.append(tuple([float(item) for item in Lines[:len(Lines) - 1].split(" ")]))
                    # converting string data type into float and making a tuple
        self.Assets[key] = values
        file.close()
        if path.exists("output.txt"):
            remove("output.txt")
        else:
            print("The file does not exist")

    def __CalculateGrade(self):
        Sum = 0
        for i in self.Absolutes.values():
            Sum += i[0]

        Sum = ceil(Sum)
        if Sum >= 90:
            self.Grade = "A"
        elif 89.0 >= Sum >= 86.0:
            self.Grade = "A-"
        elif 85.0 >= Sum >= 81.0:
            self.Grade = "B+"
        elif 80.0 >= Sum >= 77.0:
            self.Grade = "B"
        elif 76.0 >= Sum >= 72.0:
            self.Grade = "B-"
        elif 71.0 >= Sum >= 68.0:
            self.Grade = "C+"
        elif 67.0 >= Sum >= 63.0:
            self.Grade = "C"
        elif 62.0 >= Sum >= 58.0:
            self.Grade = "C-"
        elif 57.0 >= Sum >= 54.0:
            self.Grade = "D+"
        elif 53.0 >= Sum >= 50.0:
            self.Grade = "D"
        else:
            self.Grade = "F"

    # ---------------PUBLIC FUNCTIONS
    def isEmpty(self):
        return self.Empty

    def MakeReport(self):
        file = open(path.join(Directory, self.Semester + " Report.txt"), 'a')
        for item in self.Header:
            file.write(str(item) + "\n")

        Percentage = 0
        for Tuple in self.Absolutes:
            marks = self.Absolutes[Tuple]
            file.write(
                "\n" + Tuple + "\n\t|Obtained: " + str(round(marks[0], 2)) + "\n\t|Total:" + str(marks[1]) + "\n")
            Percentage += round(marks[0], 2)
        file.write("\n\t\t\t\tGrade: " + self.Grade +
                   "\n\t\t\t\tPercentage: " + str(Percentage) + "\n")
        file.close()

    def __init__(self, id, name, SemesterName, weightagesAndbestof):  # string,string,string,dict
        self.__Refresh()
        self.ID = id
        self.Name = name
        self.Semester = SemesterName
        self.WeightagesAndBestOf = weightagesAndbestof
        with open(name + ".pdf", "rb") as f:
            pdf = PDF(f)

        marks = self.__RemoveHeaderAndFooter(pdf)
        marks = TrucateString(marks)
        if not marks:
            print("No marks has been uploaded yet\n")
        else:
            if len(marks) == 0:
                self.Empty = True
            else:
                # print(marks)
                FileWriting(marks)
                self.__FileReading()
                for keys in self.Assets.keys():
                    Weightages = self.WeightagesAndBestOf[keys]
                    self.Absolutes[keys] = tuple([self.__CalculateAbsolute(keys), Weightages[1]])
                self.__CalculateGrade()
                if path.exists(name + ".pdf"):
                    remove(name + ".pdf")
                else:
                    print("The file does not exist")

    def Print(self):
        print("\n\t", self.Name, "\t", self.ID)
        for Tuple in self.Absolutes:
            marks = self.Absolutes[Tuple]
            print(Tuple, "\n\t|Obtained: ", round(marks[0], 2), "\n\t|Total:", marks[1])
        print("\nExpected Grade: ", self.Grade)


class Semesters:
    SemesterDict = {}  # SemesterName:[NoofSubjects,[List of CoursesObj]] --> List of CoursesObj: Course(CourseID, CourseName, WeightageAndBestOf)

    def __init__(self, driver):  # string, SeleniumObject
        # -------- Get SemesterName, CourseID, Name, Links
        delay = 120
        try:
            myElem = WebDriverWait(Driver, delay).until(
                EC.presence_of_element_located((By.TAG_NAME, 'tbody')))
        except TimeoutException:
            print("Loading took too much time! Coudn't find semester")
        OngoingSemester = driver.find_elements_by_xpath('/html/body/div/div/div[2]/div/div/div[2]/div/div/table/tr')
        Semester = driver.find_elements_by_tag_name('tbody')
        # -------- Getting total semester studied
        TotalSemesters = len(Semester)
        if len(OngoingSemester) != 0:
            TotalSemesters += 1
        print("Semester found: ", TotalSemesters)
        if len(OngoingSemester) != 0:
            SemesterName = OngoingSemester[1].find_element_by_tag_name('td').get_attribute(
                'innerHTML')
            if SemesterName[0] == "R":
                print(SemesterName, " Semester ", TotalSemesters, " <== Ongoing , Summer")
            else:
                print(SemesterName, " Semester ", TotalSemesters, " <== Ongoing")
            TotalSemesters -= 1
        for SemesterIndex in range(len(Semester)):
            SemesterRows = Semester[SemesterIndex].find_elements_by_tag_name('tr')
            SemesterName = SemesterRows[1].find_element_by_tag_name('td').get_attribute(
                'innerHTML')
            if SemesterName[0] == "R":
                print(SemesterName, " Semester ", TotalSemesters - SemesterIndex, " <== Summer")
            else:
                print(SemesterName, " Semester ", TotalSemesters - SemesterIndex)
        print("Enter Semester Number(s) separated by space or enter 0 to calculate ongoing semester grades: ", end="")
        SemesterName = "0"
        NoOfSubjects = 0
        Lst_Of_Sem_Grade_to_Calc = [int(item) for item in input().split()]
        # ---------- Calculating Ongoing Semester Grades
        if 0 in Lst_Of_Sem_Grade_to_Calc:
            CourseList = []
            NoOfSubjects = len(
                OngoingSemester) - 3  # -3 because first and last is dummy and second is name of semester
            for SemesterRowIndex in range(1, len(OngoingSemester) - 1,
                                          1):  # 1 index has SemesterName excluding last one because its a dummy
                CourseID = "0"
                CourseName = "0"
                if SemesterRowIndex == 1:
                    SemesterName = OngoingSemester[SemesterRowIndex].find_element_by_tag_name('td').get_attribute(
                        'innerHTML')  # Getting Semester Name
                else:
                    try:
                        myElem = WebDriverWait(Driver, delay).until(
                            EC.presence_of_element_located((By.TAG_NAME, 'tbody')))
                    except TimeoutException:
                        print("Loading took too much time! Coudn't find semester")
                    Semester = Driver.find_elements_by_tag_name(
                        'tbody')  # Doing this again because time stamp of page is changed
                    OngoingSemester = driver.find_elements_by_xpath(
                        '/html/body/div/div/div[2]/div/div/div[2]/div/div/table/tr')  # need to refresh all variables
                    Columns = OngoingSemester[SemesterRowIndex].find_elements_by_tag_name('td')
                    CourseID = Columns[0].find_element_by_tag_name('a').get_attribute(
                        'innerHTML')  # Getting Course ID
                    CourseName = Columns[1].find_element_by_tag_name('a').get_attribute(
                        'innerHTML')  # Getting Course Name
                    # ----- Going into Courses Link
                    ScrollToLink = ActionChains(Driver)
                    ScrollToLink.move_to_element(Columns[1].find_element_by_tag_name('a'))  # Scrolling to Element
                    Columns[1].find_element_by_tag_name('a').send_keys(Keys.ARROW_DOWN)
                    sleep(5)
                    Columns[1].find_element_by_tag_name('a').click()  # Clicking on Link
                    try:
                        myElem = WebDriverWait(Driver, delay).until(
                            EC.presence_of_element_located((By.XPATH, "//*[@id='app']/div/div[2]/div/div/div[2]/div["
                                                                      "1]/div/div/ul/li[2]/a")))
                    except TimeoutException:
                        print("Loading took too much time! Coudn't find Course Outline")
                    Driver.find_element_by_xpath(
                        "//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div/div/ul/li[2]/a").click()  # Clicking on Course Outline
                    try:
                        myElem = WebDriverWait(Driver, delay).until(
                            EC.presence_of_element_located((By.TAG_NAME, "table")))
                    except TimeoutException:
                        print("Loading took too much time! Coudn't find table in course outline")
                    TablesOnPage = Driver.find_elements_by_tag_name('table')  # Getting all tables on page
                    TableOfWeightageAndBestOf = TablesOnPage[
                        2]  # Weightages and bestof table is always the 3rd one i.e 2nd index
                    WABORows = TableOfWeightageAndBestOf.find_elements_by_tag_name(
                        'tr')  # Getting table rows WABO = weightage and best of
                    print("Getting Weightage and Best Of ", CourseName)
                    WeightageAndBestOf = {}
                    for WABORowIndex in range(1, len(WABORows), 1):
                        Columns = WABORows[WABORowIndex].find_elements_by_tag_name('td')
                        MarksType = Columns[0].get_attribute('innerHTML')  # Getting Marks Type
                        Weightage = Columns[1].get_attribute('innerHTML')  # Getting Weightage
                        BestOf = Columns[2].get_attribute('innerHTML')  # Getting BestOf
                        if BestOf == "Take Average of All":
                            BestOf = 0
                        WeightageAndBestOf[MarksType] = (int(BestOf), int(Weightage))
                        # print(MarksType, ":", Weightage, ",", BestOf)

                    try:
                        myElem = WebDriverWait(Driver, delay).until(
                            EC.presence_of_element_located((By.XPATH, "//*[@id='app']/div/div[2]/div/div/div[2]/div["
                                                                      "1]/div/div/ul/li[6]/a")))
                    except TimeoutException:
                        print("Loading took too much time! Coudn't find gradebook")
                    Driver.find_element_by_xpath(
                        "//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div/div/ul/li[6]/a").click()  # Clicking on GradeBook

                    try:
                        myElem = WebDriverWait(Driver, delay).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'pdf_download')))
                    except TimeoutException:
                        print("Loading took too much time! Coudn't find download button")
                    sleep(2)
                    Driver.find_element_by_class_name('pdf_download').click()  # Clicking on download Button
                    print("Getting Marks Of ", CourseName)

                    FileName = RegistrationNumber.upper() + "_StdGradeBook.pdf"
                    # print("Download Path: ",CurrentDir)
                    while 1:
                        if FileName in listdir(CurrentDir):  # Finding downloaded file
                            rename(CurrentDir + FileName,
                                   CurrentDir + CourseName + ".pdf")  # Changing its name to course name
                            # print("File Found.")
                            break
                        else:
                            sleep(1)
                    # print("Making my courses")
                    MyCourse = Course(CourseID, CourseName, SemesterName, WeightageAndBestOf)
                    if MyCourse.isEmpty() == True:
                        print("Empty Gradebook!!!!")
                    else:
                        MyCourse.Print()
                    CourseList.append(MyCourse)
                    IndexOfAllCourses = Driver.find_elements_by_xpath("//*[@id='navbar']/ul[1]/li[3]/ul/li")
                    Driver.execute_script("arguments[0].click();",
                                          Driver.find_element_by_xpath("//*[@id='navbar']/ul[1]/li[3]/ul/li[" + str(
                                              len(IndexOfAllCourses)) + "]/a"))  # Going back to View All Courses
            self.SemesterDict[SemesterName] = [NoOfSubjects, CourseList]
            exit(0)
        else:
            print("You are not currently enrolled in any ongoing semester")

        MakeFolder()
        for SemesterIndex in range(len(Semester)):
            SemesterNumber = TotalSemesters - SemesterIndex - 1
            if SemesterNumber in Lst_Of_Sem_Grade_to_Calc:
                SemesterRows = Semester[SemesterIndex].find_elements_by_tag_name('tr')  # Getting No Of Courses Studied
                NoOfSubjects = len(
                    SemesterRows) - 3  # -3 because first and last is dummy and second is name of semester
                CourseList = []
                for SemesterRowIndex in range(1, len(SemesterRows) - 1,
                                              1):  # 1 index has SemesterName excluding last one because its a dummy
                    CourseID = "0"
                    CourseName = "0"
                    if SemesterRowIndex == 1:
                        SemesterName = SemesterRows[SemesterRowIndex].find_element_by_tag_name('td').get_attribute(
                            'innerHTML')  # Getting Semester Name
                    else:
                        Columns = SemesterRows[SemesterRowIndex].find_elements_by_tag_name('td')
                        CourseID = Columns[0].find_element_by_tag_name('a').get_attribute(
                            'innerHTML')  # Getting Course ID
                        CourseName = Columns[1].find_element_by_tag_name('a').get_attribute(
                            'innerHTML')  # Getting Course Name
                        # ----- Going into Courses Link
                        ScrollToLink = ActionChains(Driver)
                        ScrollToLink.move_to_element(Columns[1].find_element_by_tag_name('a'))  # Scrolling to Element
                        Columns[1].find_element_by_tag_name('a').send_keys(Keys.ARROW_DOWN)
                        sleep(5)
                        Columns[1].find_element_by_tag_name('a').click()  # Clicking on Link
                        try:
                            myElem = WebDriverWait(Driver, delay).until(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//*[@id='app']/div/div[2]/div/div/div[2]/div["
                                               "1]/div/div/ul/li[2]/a")))
                        except TimeoutException:
                            print("Loading took too much time! Coudn't find Course Outline")
                        Driver.find_element_by_xpath(
                            "//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div/div/ul/li[2]/a").click()  # Clicking on Course Outline
                        # sleep(5)
                        try:
                            myElem = WebDriverWait(Driver, delay).until(
                                EC.presence_of_element_located((By.TAG_NAME, "table")))
                        except TimeoutException:
                            print("Loading took too much time! Coudn't find table in course outline")
                        TablesOnPage = Driver.find_elements_by_tag_name('table')  # Getting all tables on page
                        TableOfWeightageAndBestOf = TablesOnPage[
                            2]  # Weightages and bestof table is always the 3rd one i.e 2nd index
                        WABORows = TableOfWeightageAndBestOf.find_elements_by_tag_name(
                            'tr')  # Getting table rows WABO = weightage and best of
                        print("Getting Weightage and Best Of ", CourseName)
                        WeightageAndBestOf = {}
                        for WABORowIndex in range(1, len(WABORows), 1):
                            Columns = WABORows[WABORowIndex].find_elements_by_tag_name('td')
                            MarksType = Columns[0].get_attribute('innerHTML')  # Getting Marks Type
                            Weightage = Columns[1].get_attribute('innerHTML')  # Getting Weightage
                            BestOf = Columns[2].get_attribute('innerHTML')  # Getting BestOf
                            if BestOf == "Take Average of All":
                                BestOf = 0
                            WeightageAndBestOf[MarksType] = (int(BestOf), int(Weightage))
                            # print(MarksType, ":", Weightage, ",", BestOf)

                        Driver.find_element_by_xpath(
                            "//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div/div/ul/li[6]/a").click()  # Clicking on GradeBook
                        # sleep(5)
                        try:
                            myElem = WebDriverWait(Driver, delay).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'pdf_download')))
                        except TimeoutException:
                            print("Loading took too much time! Coudn't find download button")
                        sleep(2)
                        Driver.find_element_by_class_name('pdf_download').click()  # Clicking on download Button
                        print("Getting Marks Of ", CourseName)

                        FileName = RegistrationNumber.upper() + "_StdGradeBook.pdf"
                        # print("Download Path: ",CurrentDir)
                        while 1:
                            if FileName in listdir(CurrentDir):  # Finding downloaded file
                                rename(CurrentDir + FileName,
                                       CurrentDir + CourseName + ".pdf")  # Changing its name to course name
                                # print("File Found.")
                                break
                            else:
                                sleep(1)
                        # print("Making my courses")
                        if MyCourse.isEmpty() == True:
                            print("Empty Gradebook!!!!")
                        else:
                            MyCourse.MakeReport()
                        CourseList.append(MyCourse)
                        IndexOfAllCourses = Driver.find_elements_by_xpath("//*[@id='navbar']/ul[1]/li[3]/ul/li")
                        Driver.execute_script("arguments[0].click();",
                                              Driver.find_element_by_xpath("//*[@id='navbar']/ul[1]/li[3]/ul/li[" + str(
                                                  len(IndexOfAllCourses)) + "]/a"))  # Going back to View All Courses
                        # sleep(5)
                        try:
                            myElem = WebDriverWait(Driver, delay).until(
                                EC.presence_of_element_located((By.TAG_NAME, 'tbody')))
                        except TimeoutException:
                            print("Loading took too much time! Coudn't find download button")
                        Semester = Driver.find_elements_by_tag_name(
                            'tbody')  # Doing this again because time stamp of page is changed
                        SemesterRows = Semester[SemesterIndex].find_elements_by_tag_name(
                            'tr')  # need to refresh all variables
                self.SemesterDict[SemesterName] = [NoOfSubjects, CourseList]
            # break


if __name__ == '__main__':
    CurrentDir = getcwd() + '/'
    # DummyString = ''
    # for i in CurrentDir:
    #     if i == "\\":
    #         DummyString+='/'
    #     else:
    #         DummyString+=i
    # CurrentDir = DummyString
    # print(CurrentDir)
    Options = webdriver.ChromeOptions()
    Preference = {"download.default_directory": CurrentDir}
    Options.add_experimental_option("prefs", Preference)
    Driver = webdriver.Chrome(CurrentDir + "chromedriver",options=Options)

    print("Opening Portal")
    Driver.get("http://portal.ucp.edu.pk")

    delay = 120  # seconds
    try:
        myElem = WebDriverWait(Driver, delay).until(EC.presence_of_element_located((By.ID, 'submit')))
    except TimeoutException:
        print("Loading took too much time!")
    print("Portal Opened")
    RegistrationNumber = input("Enter Registration Number: ")
    Password = input("Enter Password: ")
    degree_name = SetDegree(RegistrationNumber)
    degree_name = degree_name.upper()
    InputRegistration = Driver.find_element_by_xpath('//input[@placeholder="Registration Number"]')
    InputRegistration.send_keys(RegistrationNumber)
    InputPassword = Driver.find_element_by_xpath('//input[@placeholder="Password"]')
    InputPassword.send_keys(Password)
    Driver.find_element_by_id('submit').click()

    delay = 120  # seconds
    try:
        myElem = WebDriverWait(Driver, delay).until(EC.presence_of_element_located((By.XPATH, "//*[@id='navbar']/ul[1]/li[3]/ul/li")))
    except TimeoutException:
        print("Couldn't click All Courses tab because of slow internet")
    IndexOfAllCourses = Driver.find_elements_by_xpath("//*[@id='navbar']/ul[1]/li[3]/ul/li")
    Driver.execute_script("arguments[0].click();",
                          Driver.find_element_by_xpath(
                              "//*[@id='navbar']/ul[1]/li[3]/ul/li[" + str(len(IndexOfAllCourses)) + "]/a"))
    Degree = Semesters(Driver)
    # input()
