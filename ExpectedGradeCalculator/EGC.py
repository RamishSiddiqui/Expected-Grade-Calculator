import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import os


class Course:
    Name = "0"
    ID = "0"
    Assets = {} #For Marks Name:pandas.DataFrame
    WeightagesAndBestOf = {} # Name:(Best Of, Weightage)
    Absolutes = {} # Name:(Obtained Absolute, Weightage)
    Grade = "0"

    def __init__(self, id, name, weightagesAndbestof): # string,string,dict
        self.ID = id
        self.Name = name
        self.WeightagesAndBestOf = weightagesAndbestof

    def CalculateGrade(self):
        Sum = 0
        for i in self.Absolutes.values():
            Sum+=i[0]
        if Sum >= 90:
            self.Grade = "A"
        elif 86 <= Sum < 90:
            self.Grade = "A-"
        elif 81 <= Sum < 86:
            self.Grade = "B+"
        elif 76 <= Sum <= 80:
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

    def Print(self):
        print(self.Name,"\t",self.ID)
        for Tuple in self.Absolutes:
            print(Tuple,"\t",self.Absolutes[Tuple])
        print("\nExpected Grade: ",self.Grade)

class Semesters:
    SemesterDict = {} # SemesterName:[NoofSubjects,[List of CoursesObj]]

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
                    time.sleep(2)
                    Columns[1].find_element_by_tag_name('a').click()  # Clicking on Link
                    Driver.find_element_by_xpath(
                        "//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div/div/ul/li[2]/a").click()  # Clicking on Course Outline
                    time.sleep(5)
                    TablesOnPage = Driver.find_elements_by_tag_name('table')  # Getting all tables on page
                    TableOfWeightageAndBestOf = TablesOnPage[
                        2]  # Weightages and bestof table is always the 3rd one i.e 2nd index
                    WABORows = TableOfWeightageAndBestOf.find_elements_by_tag_name(
                        'tr')  # Getting table rows WABO = weightage and best of
                    WeightageAndBestOf = {}
                    for WABORowIndex in range(1, len(WABORows), 1):
                        Columns = WABORows[WABORowIndex].find_elements_by_tag_name('td')
                        MarksType = Columns[0].get_attribute('innerHTML')  # Getting Marks Type
                        Weightage = Columns[1].get_attribute('innerHTML')  # Getting Weightage
                        BestOf = Columns[2].get_attribute('innerHTML')  # Getting BestOf
                        if BestOf == "Take Average of All":
                            BestOf = 0
                        WeightageAndBestOf[MarksType] = (int(BestOf), int(Weightage))
                        #print(MarksType, ":", Weightage, ",", BestOf)
                    MyCourse = Course(CourseID, CourseName, WeightageAndBestOf)
                    CourseList.append(MyCourse)

                    Driver.find_element_by_xpath(
                        "//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div/div/ul/li[6]/a").click()  # Clicking on GradeBook
                    time.sleep(5)
                    Driver.find_element_by_class_name('pdf_download').click()  # Clicking on download Button
                    time.sleep(2)
                    FileName = RegistrationNumber.upper() + "_StdGradeBook.pdf"
                    while 1:
                        if FileName in os.listdir(CurrentDir):  # Finding downloaded file
                            os.rename(CurrentDir + FileName,
                                      CurrentDir + CourseName + ".pdf")  # Changing its name to course name
                            break
                        else:
                            time.sleep(1)

                    Driver.execute_script("arguments[0].click();",
                                          Driver.find_element_by_xpath(
                                              "//*[@id='navbar']/ul[1]/li[3]/ul/li/a"))  # Going back to View All Courses
                    time.sleep(5)
                    Semester = Driver.find_elements_by_tag_name(
                        'tbody')  # Doing this again because time stamp of page is changed
                    SemesterRows = Semester[SemesterIndex].find_elements_by_tag_name('tr')  # need to refresh all variables
            self.SemesterDict[SemesterName] = [NoOfSubjects, CourseList]


if __name__ == '__main__':
    CurrentDir = os.getcwd() + '/'
    print(CurrentDir)
    Options = webdriver.ChromeOptions()
    Preference = {"download.default_directory": CurrentDir}
    Options.add_experimental_option("prefs", Preference)
    Driver = webdriver.Chrome(CurrentDir + "chromedriver.exe", options=Options)

    print("Opening Portal")
    Driver.get("http://portal.ucp.edu.pk")

    delay = 120  # seconds
    try:
        myElem = WebDriverWait(Driver, delay).until(EC.presence_of_element_located((By.ID, 'submit')))
        print("Page is ready!")
    except TimeoutException:
        print("Loading took too much time!")

    print("Portal Opened")
    time.sleep(2)
    InputRegistration = Driver.find_element_by_xpath('//input[@placeholder="Registration Number"]')
    RegistrationNumber = 'L1F17BSCS0103'  # <------------------------------------------------Enter Registration
    InputRegistration.send_keys(RegistrationNumber)
    InputPassword = Driver.find_element_by_xpath('//input[@placeholder="Password"]')
    Password = 'RdwiaGSN'  # <-----------------------------------------------------Enter Password
    InputPassword.send_keys(Password)
    Driver.find_element_by_id('submit').click()

    time.sleep(4)
    Driver.execute_script("arguments[0].click();",
                          Driver.find_element_by_xpath("//*[@id='navbar']/ul[1]/li[3]/ul/li/a"))

    time.sleep(5)
    #WebSemesters = Driver.find_elements_by_tag_name('tbody')
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
    # time.sleep(3)
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
    # time.sleep(3)
    # Driver.find_element_by_class_name('pdf_download').click()
    # time.sleep(2)
    # FileName = RegistrationNumber.upper() + "_StdGradeBook.pdf"
    # while 1:
    #     if FileName in os.listdir(CurrentDir):
    #         os.rename(CurrentDir + FileName,CurrentDir + 'Os.pdf')
    #         break
    #     else:
    #         time.sleep(1)
    # Driver.execute_script('window.history.go(-3)')

    Degree = Semesters(Driver)