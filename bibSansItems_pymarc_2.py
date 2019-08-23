import csv
import pymarc
from pymarc import MARCReader
from pymarc import MARCWriter
from pymarc import Record
from pymarc.field import Field
import datetime


###################
#    Functions
###################

def readCsvFile(fileName):
    myFile = open(fileName, "r", encoding = "utf-8", errors = "ignore")
    reader = csv.reader(myFile)

    return reader

def readTextFile(fileName):
    myFile = open(fileName, "r", encoding = "utf-8", errors = "ignore")
    reader = myFile.read()

    return reader

def createPrintFiles(filename, x):
    myFile = open(filename, x, newline = "", encoding="utf-8", errors= "ignore")
    writer = csv.writer(myFile)

    return writer

def transferToLoansArray(reader):
    myArray = []
    for row in reader:
        myArray.append([row[0], row[1], row[2]])
    return myArray

def transferDeletedItems(reader):
    deletedItems = []
    deletedItems = reader.split("\n")
    return deletedItems

def cleanSysNumber(SystemNumber):
    if SystemNumber.startswith("=001"):
        SystemNumber = SystemNumber[4:]
        SystemNumber = SystemNumber.strip()
    return SystemNumber


def treatLeader(myLeader):
    leaderInfo = leader[7]
    if leaderInfo == "m" or leaderInfo == "a" or leaderInfo == "c" or leaderInfo == "i":
        mySubfieldM = "BOOK"
    elif leaderInfo == "s" :
        mySubfieldM = "ISSUE"
    else:
        mySubfieldM = "FIND ME"
    return mySubfieldM


def assignOneField(record, field, subfield):
    try: 
        myField = record[field][subfield]
    except TypeError:
        myField = ""
    return myField

def assignMultipleFieldsSubfield(record, field, subfield):
    myArray = []
    for currentField in record.get_fields(field):
        for currentSubfield in currentField.get_subfields(subfield):
            myArray.append(currentSubfield)
    return myArray

def assignMultipleSubfields(record, field, subfield1, subfield2, subfield3):
    myArray = []
    for currentField in record.get_fields(field):
        myArray = []
        for currentSubfield in currentField.get_subfields(subfield1, subfield2, subfield3):
            myArray.append(currentSubfield)
    return myArray

def dealWithSubfields(myArray, systemNumber, multiplesDict):
    if len(myArray) > 1:
        mySubfield = myArray[0]
        if systemNumber not in multiplesDict:
            multiplesDict[systemNumber] = myArray
        else:
           multiplesDict[systemNumber] = multiplesDict[systemNumber] + myArray 
    elif len(myArray) == 1 :
        mySubfield = myArray[0]
    elif len(myArray) == 0:
        mySubfield = ""
    return mySubfield


def createBarcode(number):
    barcode = "CTC"
    
    x = 8 - len(str(number))
    myStr = ""
    for i in range(0, x):
        myStr = myStr + "0"
    
    barcode = barcode + myStr + str(number)
    return barcode

def findLoanStatus(subfield1, subfield2, LoanStatusList):
    loanStatus = ""
    for currentArray in LoanStatusList:
        if subfield1 == currentArray[0] and subfield2 == currentArray[1]:
            loanStatus = currentArray[2]
    return loanStatus


###################
#    Main Code   
###################

LoanCodeDict = {
    "01": "Regular Loan", 
    "02": "Journal Loan", 
    "04": "In Library Use", 
    "05": "By Consultation", 
    "07": "No Circ Info", 
    "08" : "In Library Use", 
    "20": "2 day Reserve Loan", 
    "21": "Regular Loan", 
    "50" : "Audio/Video & Map Loan",
    "x" : "Find me"}

multiple930Needed = {}
deletedItems = []

loanStatusReader = readCsvFile("LoanStatuses.csv")
LoanStatusList = transferToLoansArray(loanStatusReader)

deletedItemsreader = readTextFile("deleted_items_list_20190110.txt")
deletedItems = transferDeletedItems(deletedItemsreader)

SerialsRecordsWriter = MARCWriter(open("itemCreatedSerials.mrc", "wb"))
BooksRecordsWriter = MARCWriter(open("itemCreatedBooks.mrc", "wb"))
myErrorFile = createPrintFiles("myErrorFile.csv", "w")
mydeletesFile = createPrintFiles("deletedItemsFile.csv", "w")
myMultipleFile = createPrintFiles("multiple930Needed.csv", "w")
myWriterFile = createPrintFiles("itemsCreated.csv", "w")

file = open("bibssansitems_with852.mrc", "rb")
reader = MARCReader(file, to_unicode= True, force_utf8= True, utf8_handling="strict")

number = 1 
for record in reader:

    if record["852"] and not record["930"]:

        SystemNum = str(record["001"])
        SysNum = cleanSysNumber(SystemNum)

        if SysNum not in deletedItems:

            collection = assignMultipleFieldsSubfield(record, "852", "b")
            subfield1 = dealWithSubfields(collection, SysNum, multiple930Needed)

            shelvingLocation = assignMultipleFieldsSubfield(record, "852", "c")
            subfield2 = dealWithSubfields(shelvingLocation, SysNum, multiple930Needed)

            if subfield2 == "":
                myErrorFile.writerow([SysNum, "No Specific Location Information (852$c)"])
            elif subfield1 == "DBASE":
                mydeletesFile.writerow([SysNum, "DBASE"])
            else:
                subfieldl = "MGU01"
                subfieldL = "MUSE"
            
                leader= record.leader
                subfieldm = treatLeader(leader)
                if subfieldm == "FIND ME":
                    myErrorFile.writerow([SysNum, "new LDR # 8 value"])
                else:    
                    classification = assignMultipleFieldsSubfield(record, "852", "h")
                    subfieldh = dealWithSubfields(classification, SysNum, multiple930Needed)

                    itemNumber = assignMultipleFieldsSubfield(record, "852", "i")
                    subfieldi = dealWithSubfields(itemNumber, SysNum, multiple930Needed)

                    subfield5 = createBarcode(number)
                    number = number + 1

                    subfield8 = str(datetime.datetime.now().strftime("%y%m%d%H%M%S"))

                    subfieldf = findLoanStatus(subfield1, subfield2, LoanStatusList)

                    if subfieldf == "x":
                        myErrorFile.writerow([SysNum, "x loan status code"])
                    elif subfieldf == "":
                        myErrorFile.writerow([SysNum, "Unknown Loan Status"])
                        subfieldF = ""
                    else:
                        subfieldF = LoanCodeDict[subfieldf]
                    
                        holdingsData = str(record["852"])
                        subfieldw = holdingsData[6]
                    

                        myfield = Field(tag = "930", indicators= [" ", "1"], subfields=[
                            "l", subfieldl,
                            "L", subfieldL,
                            "m", subfieldm,
                            "1", subfield1,
                            "2", subfield2,
                            "h", subfieldh,
                            "i", subfieldi,
                            "5", subfield5,
                            "8", subfield8,
                            "f", subfieldf,
                            "F", subfieldF,
                            "w", subfieldw
                        ])

                        record.add_field(myfield)
                        myWriterFile.writerow([SysNum, subfieldm, subfield1, subfield2, subfield5, "item added"])

                        if subfieldm == "ISSUE":
                            SerialsRecordsWriter.write(record)

                        elif subfieldm == "BOOK": 
                            BooksRecordsWriter.write(record)
                        

        else:
            mydeletesFile.writerow([SysNum, "a deleted item match"]) 
    else:
        SystemNum = str(record["001"])
        SysNum = cleanSysNumber(SystemNum)
        myErrorFile.writerow([SysNum, "no 852 or a 930"]) 


for keys in multiple930Needed:
    myMultipleFile.writerow([keys, multiple930Needed[keys]])

SerialsRecordsWriter.close()
BooksRecordsWriter.close()
