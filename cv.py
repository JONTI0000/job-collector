from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import constants as const
import csv
import pandas as pd
import os
import cv2
import pytesseract
 

class Sender(webdriver.Chrome):
    def __init__(self) -> None:
        super().__init__(service=ChromeService(ChromeDriverManager().install()))
        self.implicitly_wait(15)
        self.maximize_window()
        self.current_window=self.current_window_handle
        self.ads=[]
        self.data={}

    def land_page(self):
        """getting to the main page of top jobs the index page"""
        self.get(const.BASE_URL)

    def search_keyword(self,keyword:str):
        """search the relavent keyword in the search box
        takes the keyword(str) as an argument no default argument given"""
        search=self.find_element(By.ID,"txtKeyWord")
        search.send_keys(keyword)
        button=self.find_element(By.ID,"btnSearch")
        button.click()

    def get_ads(self):
        """gets the list of ads and appends it to a list
        at class level data structure"""
        for i in range(0,25):#for the time being it only takes the first few ads gotta figure out 
            ad=self.find_element(By.ID,"tr"+str(i))
            data=self.get_data(i)
            if self.presence_check(self.data.get("job_ref_no")):
                self.record_data()
                ActionChains(self)\
                    .click(ad)\
                    .perform()
                self.switch()
                self.save_ad()
                self.switch_to.window(self.current_window)
            else:
                continue
        
    def record_data(self):
        """record the data at a instance level to a csv file called addetails"""
        data=[self.data.get("job_ref_no"),self.data.get("position"),self.data.get("company")]
        fhandle=open(const.TEXT_DOCUMENT,"a",newline="")
        writer=csv.writer(fhandle)
        writer.writerow(data)
        fhandle.close()
    
    def presence_check(self,id):
        """does a presence check on the ads to see if there is any redundancy in the ad downloading by making sure there is no
        repetition of the job reference number by reffering to the CSV file"""
        df=pd.read_csv(const.TEXT_DOCUMENT)
        for i in df["job reference no"]:
            if i==int(id):
                return False
        return True

    def switch(self):
        """switches the window from the main to the vacancy window"""
        chwd = self.window_handles

        for w in chwd:
    
           if(w!=self.current_window):
            self.switch_to.window(w)
            self.maximize_window()
            self.implicitly_wait(15)

    
    def get_image_name(self):
        """returns the job post for the image name"""
        return self.find_element(By.XPATH,"//h3[@id='position']").text


    def save_ad(self):
        """saves a screenshot of the ad into a folder called ads using the job reference number as the file name"""
        try:
            img=self.find_element(By.XPATH,"//div[@id='remark']/p/img")
        except:
            img=self.find_element(By.XPATH,"//div[@id='remark']/p/a/img ")
        src=img.get_attribute("src")
        self.get(src)
        self.save_screenshot(const.IMG_LOC+"{}.png".format(self.data.get("job_ref_no")))

    def go_to_ad(self):
        """clicks on the ads by iterating throught the list of ads"""
        for i in self.ads:#this approach just tries to go through all the ads at once not the best approach gotta adjust
            ActionChains(self)\
                .click(i)\
                .perform()
            self.switch()
            self.save_ad()
            self.switch_to.window(self.current_window)
        

    def get_data(self,i):
        """assigns the job ref no,position,company to a dictionary at the instance level"""
        job_ref_no=self.find_element(By.XPATH,"//tr[@id='tr{}']/td[@width='5%']".format(i)).text
        position=self.find_element(By.XPATH,"//tr[@id='tr{}']/td/h2/span".format(i)).text
        company=self.find_element(By.XPATH,"//tr[@id='tr{}']/td/h1".format(i)).text
        self.data={
            "job_ref_no":job_ref_no,
            "position":position,
            "company":company
        }
        return self.data



#this is the next few steps in functions since i have no clue on how to
#implement this using classes yet

def get_text(img_path:str,job_ref_no):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe" 
    #image read
    img = cv2.imread(img_path)
    # Preprocessing the image starts
    # Convert the image to gray scale
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # Performing OTSU threshold
    ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    # Specify structure shape and kernel size.
    # Kernel size increases or decreases the area
    # of the rectangle to be detected.
    # A smaller value like (10, 10) will detect
    # each word instead of a sentence.
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))
    # Applying dilation on the threshold image
    dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)
    # Finding contours
    contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_NONE)
    # Creating a copy of image
    im2 = img.copy()
    # A text file is created and flushed
    file = open(const.TEXT_DOCUMENT, "a")
    file.write("")
    file.close()
    # Looping through the identified contours
    # Then rectangular part is cropped and passed on
    # to pytesseract for extracting text from it
    # Extracted text is then written into the text file
    for cnt in contours: x, y, w, h = cv2.boundingRect(cnt)
    # Drawing a rectangle on copied image
    rect = cv2.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)
    # Cropping the text block for giving input to OCR
    cropped = im2[y:y + h, x:x + w]
    # Open the file in append mode
    file = open("recognized.txt","a")
    # Apply OCR on the cropped image
    text = pytesseract.image_to_string(cropped)
    # Appending the text into file
    file.write(job_ref_no)
    file.write("\n")
    file.write(text)
    file.write("\n")
    # Close the file
    file.close()


def get_folder_list():
    """get the list of files in a given file path"""        
    current_path=os.getcwd()
    os.chdir(os.path.join(current_path,r"CV sender\ads"))
    return os.listdir(os.getcwd())

def write_ad_details():
    for ad in get_folder_list():
        if ad.endswith(".txt"):
            continue
        img_path=os.path.join(os.getcwd(),ad)
        job_ref_no=ad.replace(".png","")
        get_text(img_path,job_ref_no)

write_ad_details()

