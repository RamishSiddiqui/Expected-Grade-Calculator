from time import sleep
from os import getcwd, rename, listdir, remove
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from pdftotext import PDF
from getpass import getpass

degree_name = ""


def SetDegree(RegisterationNumber):
    return RegisterationNumber[5:7]


def RemoveHeaderAndFooter(pdf):
    marks = []
    for page in pdf:
        # ------------- this is to remove header
        index = page.rindex(degree_name)  # find index of the BS(last word in header)
        page = page[index + 3:len(page)]  # slice the string uptil BS

        # ------------- this is to remove footer
        index = page.find("Page")  # find the index of the page(first word in footer)
        page = page[0:index]  # slice the string
        marks.append(page)  # converting PDF type object in list of string
    return marks


def TrucateString(marks):
    # ------------- removing all : and spaces from the string
    marks = [line.strip().split("\n") for line in marks]                # make string list
    marks= [item for sublist in marks for item in sublist]              # above line make list of list thereefore converting it back to the list
    for i in range(len(marks)):
        marks[i] = marks[i].replace(':', '')                                # replacing all : into spaces
        temp=str(marks[i]).maketrans("\n\t\r", "   ")
        marks[i]= marks[i].translate(temp)
        marks[i]=' '.join([x for x in marks[i].split(' ') if len(x) > 0])
    marks=[i for i in marks if i!='']                                   # removing all extra spaces in the string.
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
    Assets = {}  # For Marks Name:(obtained, Total)
    WeightagesAndBestOf = {}  # Name:(Best Of, Weightage)
    Absolutes = {}  # Name:(Obtained Absolute, Weightage)
    Grade = "0"
    Percentage = 0.0

    # ---------------PRIVATE FUNCTIONS
    def __CalculateAbsolute(self, field):  # field: quiz, assignment etc
        # ------------- Calculating the absolute markks in the given field
        marks = self.Assets[field]
        marks.sort(key=lambda x: x[0] / x[1], reverse=False)
        Best_of = self.WeightagesAndBestOf[field]
        if Best_of[0] != 0:
            marks = marks[:Best_of[0]]
        Total = 0  # Calculcating sum
        Obtain = 0
        for i in marks:
            Total += i[0]
            Obtain += i[1]
        return (Obtain / Total) * (Best_of[1])

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
        remove("output.txt")

    def __CalculateGrade(self):
        Sum = 0
        for i in self.Absolutes.values():
            Sum += i[0]
        self.Percentage = Sum
        if Sum >= 90:
            self.Grade = "A"
        elif Sum >= 86 and Sum < 90:
            self.Grade = "A-"
        elif Sum >= 81 and Sum < 86:
            self.Grade = "B+"
        elif Sum >= 76 and Sum < 80:
            self.Grade = "B"
        elif 71 <= Sum <= 75:
            self.Grade = "B-"
        elif 66 <= Sum <= 70:
            self.Grade = "C+"
        elif 61 <= Sum <= 65:
            self.Grade = "C"
        elif 56 <= Sum <= 50:
            self.Grade = "C-"
        elif 50 <= Sum <= 55:
            self.Grade = "D"
        else:
            self.Grade = "F"

    def __Print(self):
        print("\t", self.Name, "\t", self.ID)
        for Tuple in self.Absolutes:
            marks = self.Absolutes[Tuple]
            print(Tuple, "\t", round(marks[0], 2),"/", marks[1])
        print("\nPercentage: ", self.Percentage, "\nExpected Grade: ", self.Grade)

    def __ResetAttributes(self):
        self.Name = "0"
        self.ID = "0"
        self.Assets = {}  # For Marks Name:(obtained, Total)
        self.WeightagesAndBestOf = {}  # Name:(Best Of, Weightage)
        self.Absolutes = {}  # Name:(Obtained Absolute, Weightage)
        self.Grade = "0"
        self.Percentage = 0.0

    # ---------------PUBLIC FUNCTIONS
    def __init__(self, id, name, weightagesAndbestof):  # string,string,dict
        self.__ResetAttributes()
        self.ID = id
        self.Name = name
        self.WeightagesAndBestOf = weightagesAndbestof
        with open(name + ".pdf", "rb") as f:
            pdf = PDF(f)

        marks = RemoveHeaderAndFooter(pdf)
        marks = TrucateString(marks)
        FileWriting(marks)
        self.__FileReading()
        for keys in self.Assets.keys():
            Weightages = self.WeightagesAndBestOf[keys]
            self.Absolutes[keys] = tuple([self.__CalculateAbsolute(keys), Weightages[1]])
        self.__CalculateGrade()
        remove(name + ".pdf")
        self.__Print()


class Semesters:
    SemesterDict = {}  # SemesterName:[NoofSubjects,[List of CoursesObj]] --> List of CoursesObj: Course(CourseID, CourseName, WeightageAndBestOf)

    def __init__(self, driver):  # string, SeleniumObject
        # -------- Get SemesterName, CourseID, Name, Links
        Semester = driver.find_elements_by_tag_name('tbody')
        SemesterName = "0"
        NoOfSubjects = 0
        for SemesterIndex in range(len(Semester)):
            SemesterRows = Semester[SemesterIndex].find_elements_by_tag_name('tr')  # Getting No Of Courses Studied
            NoOfSubjects = len(SemesterRows) - 3  # -3 because first and last is dummy and second is name of semester
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
                    CourseID = Columns[0].find_element_by_tag_name('a').get_attribute('innerHTML')  # Getting Course ID
                    CourseName = Columns[1].find_element_by_tag_name('a').get_attribute(
                        'innerHTML')  # Getting Course Name
                    # ----- Going into Courses Link
                    ScrollToLink = ActionChains(Driver)
                    ScrollToLink.move_to_element(Columns[1].find_element_by_tag_name('a'))  # Scrolling to Element
                    Columns[1].find_element_by_tag_name('a').send_keys(Keys.ARROW_DOWN)
                    sleep(5)
                    Columns[1].find_element_by_tag_name('a').click()  # Clicking on Link
                    Driver.find_element_by_xpath(
                        "//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div/div/ul/li[2]/a").click()  # Clicking on Course Outline
                    sleep(5)
                    TablesOnPage = Driver.find_elements_by_tag_name('table')  # Getting all tables on page
                    TableOfWeightageAndBestOf = TablesOnPage[
                        2]  # Weightages and bestof table is always the 3rd one i.e 2nd index
                    WABORows = TableOfWeightageAndBestOf.find_elements_by_tag_name(
                        'tr')  # Getting table rows WABO = weightage and best of
                    print("Getting Weightage and Best Of ",CourseName)
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
                    sleep(5)
                    Driver.find_element_by_class_name('pdf_download').click()  # Clicking on download Button
                    print("Getting Marks Of ",CourseName)
                    sleep(2)
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
                    MyCourse = Course(CourseID, CourseName, WeightageAndBestOf)
                    CourseList.append(MyCourse)
                    Driver.execute_script("arguments[0].click();",
                                          Driver.find_element_by_xpath(
                                              "//*[@id='navbar']/ul[1]/li[3]/ul/li/a"))  # Going back to View All Courses
                    sleep(5)
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
    print(CurrentDir)
    Options = webdriver.ChromeOptions()
    Preference = {"download.default_directory": CurrentDir}
    Options.add_experimental_option("prefs", Preference)
    Driver = webdriver.Chrome(CurrentDir + "chromedriver",options=Options)

    print("Opening Portal")
    Driver.get("http://portal.ucp.edu.pk")

    delay = 120  # seconds
    try:
        myElem = WebDriverWait(Driver, delay).until(EC.presence_of_element_located((By.ID, 'submit')))
        print("Page is ready!")
    except TimeoutException:
        print("Loading took too much time!")

    print("Portal Opened")
    sleep(5)
    RegistrationNumber = input("Enter Registration Number: ")
    Password = input("Enter Password: ")
    degree_name = SetDegree(RegistrationNumber)
    degree_name = degree_name.upper()
    InputRegistration = Driver.find_element_by_xpath('//input[@placeholder="Registration Number"]')
    InputRegistration.send_keys(RegistrationNumber)
    InputPassword = Driver.find_element_by_xpath('//input[@placeholder="Password"]')
    InputPassword.send_keys(Password)
    Driver.find_element_by_id('submit').click()

    sleep(5)
    Driver.execute_script("arguments[0].click();",
                          Driver.find_element_by_xpath("//*[@id='navbar']/ul[1]/li[3]/ul/li/a"))

    sleep(5)
    # WebSemesters = Driver.find_elements_by_tag_name('tbody')
    # print(Semesters)
    #
    # a = Semesters[0].find_elements_by_tag_name('tr')
    # print(len(a),"\n",a)
    # b = a[1].find_elements_by_tag_name('td')
    # print(len(b),b)
    # print(b[0].get_attribute('innerHTML'))

    # for i in range(1,len(a) - 1,1):
    #     if i == 1:
    #         SemesterName = a[1].find_elements_by_tag_name('td')[0].get_attribute('innerHTML')
    #     else:
    #

    # b = a[2].find_elements_by_tag_name('td')
    # link = b[0].find_element_by_tag_name('a').click()
    #
    # Driver.find_element_by_xpath("//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div/div/ul/li[2]/a").click()
    # sleep(5)
    # TablesOnPage = Driver.find_elements_by_tag_name('table')
    #
    # TableOfWeightageAndBestOf = TablesOnPage[2]
    # Rows = TableOfWeightageAndBestOf.find_elements_by_tag_name('tr')
    # for RowIndex in range(1,len(Rows),1):
    #     Columns = Rows[RowIndex].find_elements_by_tag_name('td')
    #     print(len(Columns))
    #     MarksType = Columns[0].get_attribute('innerHTML')
    #     Weightage = Columns[1].get_attribute('innerHTML')
    #     BestOf = Columns[2].get_attribute('innerHTML')
    #     print(MarksType,":",Weightage,",",BestOf)

    # Driver.find_element_by_xpath("//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div/div/ul/li[6]/a").click()
    # time.sleep(5)
    # Driver.find_element_by_class_name('pdf_download').click()
    # time.sleep(5)
    # FileName = RegistrationNumber.upper() + "_StdGradeBook.pdf"
    # while 1:
    #     if FileName in os.listdir(CurrentDir):
    #         rename(CurrentDir + FileName,CurrentDir + 'Os.pdf')
    #         break
    #     else:
    #         time.sleep(5)
    # Driver.execute_script('window.history.go(-3)')

    Degree = Semesters(Driver)
    input()
