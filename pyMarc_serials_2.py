import csv
import pymarc
from pymarc import MARCReader
from pymarc import MARCWriter
from pymarc import Record
from pymarc.field import Field
import os
import copy
import re

###################
#    Functions
###################

def createPrintFiles(filename):
    myFile = open(filename, "w", newline = "", encoding="utf-8", errors= "ignore")
    writer = csv.writer(myFile)

    return writer


def cleanOclcNum(array):
    matchFound = False
    for currentField035a in array:
        currentField035a = currentField035a.strip()
        if currentField035a.startswith("(OCoLC)"):
            oclcNum = currentField035a[7:]
            matchFound = True
    if matchFound == False:
       oclcNum = "; ".join(str(x) for x in array)
    return oclcNum

def cleanSysNumber(SystemNumber):
    if SystemNumber.startswith("=001"):
        SystemNumber = SystemNumber[4:]
        SystemNumber = SystemNumber.strip()
    return SystemNumber

def createBarcode(number):
    barcode = "CTCC"
    
    x = 7 - len(str(number))
    myStr = ""
    for i in range(0, x):
        myStr = myStr + "0"
    
    barcode = barcode + myStr + str(number)
    return barcode 

def assignOneField(record, field, subfield):
    try: 
        myField = record[field][subfield]
    except TypeError:
        myField = ""
    return myField

def assignMultipleFields(record, field, subfield):
    myArray = []
    for currentField in record.get_fields(field):
        for currentSubfield in currentField.get_subfields(subfield):
            myArray.append(currentSubfield)
    return myArray

def treatMyStatus(record, field, subfield, Status):
    myArray = []
    for currentField in record.get_fields(field):
        for currentSubfield in currentField.get_subfields(subfield):
            if currentSubfield == Status:
                myArray.append(currentField)
    return myArray

def removeFields(myArray1, myArray2, myArray3, record):
    global rowsDeleted
    recordChanged = False
    if len(myArray1) > 0:
        for currentSlot in myArray1:
            if currentSlot != "":
                record.remove_field(currentSlot)
                recordChanged = True
                rowsDeleted = rowsDeleted + 1
    if len(myArray2) > 0:
        for currentSlot in myArray2:
            if currentSlot != "":
                record.remove_field(currentSlot)
                recordChanged = True
                rowsDeleted = rowsDeleted + 1
    if len(myArray3) > 0:
        for currentSlot in myArray3:
            if currentSlot != "":
                record.remove_field(currentSlot)
                recordChanged = True
                rowsDeleted = rowsDeleted + 1
    return recordChanged

def findIterationsOfYears(myAArray, mySArray, myFinalAArray, myFinalSArray):
    for currentSubfield in myAArray:       
        myFinalAArray.extend(re.findall("([12][06-9]\d\d[-\/]?[12]?[06-9]?\d?\d?)", currentSubfield))
    for currentSubfield in mySArray:
        myFinalSArray.extend(re.findall("([12][06-9]\d\d[-\/]?[12]?[06-9]?\d?\d?)", currentSubfield))


def treatYearRanges(Separator, myNote, myArray):
    y = myNote.split(Separator)
    if len(y[1]) == 4:
        for numbers in range(int(y[0]), int(y[1]) + 1):
            if not str(numbers).startswith("10"):
                myArray.append(str(numbers))
    elif len(y[1]) == 2:
        u = int(y[0][:2] + y[1]) + 1
        for numbers in range(int(y[0]), u):
            if not str(numbers).startswith("10"):
                myArray.append(str(numbers))
    elif len(y[1]) == 1:
        u = int(y[0][:3] + y[1]) + 1
        for numbers in range(int(y[0]), u):
            if not str(numbers).startswith("10"):
                myArray.append(str(numbers))

def  rebuildYearArray(myArray):           
    myCurrentList = myArray
    myArray = []

    for currentIter in myCurrentList:
        if "/" in currentIter:
            treatYearRanges("/", currentIter, myArray)
        elif "-" in currentIter:
            treatYearRanges("-", currentIter, myArray)
        elif re.match("([12][06-9]\d\d)", currentIter):
            if not currentIter.startswith("10"):
                myArray.append(currentIter)

    if myArray == []:
        myArray = myCurrentList
    return myArray

def cleanUpArrays(myArray):
    myArray = list(set(myArray))
    myArray = sorted(myArray)
    return myArray  

###################
#    Main Code   
###################

csvFileWriter = createPrintFiles("coverageAnalysis_Results.csv")
csvFileWriter.writerow(["System Number", "Oclc Number", "Title", "866 subfield A", "930 subfield S", "Analysis result"])
onlyFileWriter = createPrintFiles("all_explained.csv")
onlyFileWriter.writerow(["System Number", "Oclc Number", "Title","866 subfield A", "930 subfield S", "How was record manipulated"])
deleted930FileWriter = createPrintFiles("deletedItems.csv")
deleted930FileWriter.writerow(["System Number", "Oclc Number", "Title", "A 930 deleted due to status"])

changedRecordsWriter = MARCWriter(open("changedRecord.mrc", "wb"))
unchangedRecordsWriter = MARCWriter(open("unchangedRecord.mrc", "wb"))
deletedRecordsWriter = MARCWriter(open("deletedRecord.mrc", "wb"))

rowsDeleted = 0
rowsAdded = 0



currentDir = os.getcwd()
filesDir = currentDir + "\\files\\"


for filename in os.listdir(filesDir):
    print(filename)
    sysNumCountArray = []
    originalItemCount = 0
    finalItemCount = 0
    
    file = open(filesDir + filename, "rb")
    reader = MARCReader(file, to_unicode = True, force_utf8= True)

    number = 1

    for record in reader:
        myRecord = []
        subfieldS = []
        subfieldA = []

        #Match basic fields
        SystemNum = str(record["001"])
        SysNum = cleanSysNumber(SystemNum)
        if SysNum not in sysNumCountArray:
            sysNumCountArray.append(SysNum)
        oclc = assignMultipleFields(record, "035", "a")
        OclcNum = cleanOclcNum(oclc)
        title = assignOneField(record, "245", "a")

        
        items = record.get_fields("930")
        originalItemCount = originalItemCount + len(items)

        #Remove the 930's with the Status Not arrived or Claimed
        NaStatuses = treatMyStatus(record, "930", "P", "Not arrived")
        NAStatuses = treatMyStatus(record, "930", "P", "Not Arrived")
        ClStatuses = treatMyStatus(record, "930", "P", "Claimed")
        recordChanged = removeFields(NaStatuses, NAStatuses, ClStatuses, record)
        if recordChanged == True:
            myRecord = [SysNum, OclcNum, title, "A 930 deleted due to status"]
            deleted930FileWriter.writerow(myRecord)
        
        if record["930"] is not None:

            subfieldA = assignMultipleFields(record, "866", "a")
            subfieldS = assignMultipleFields(record, "930", "s")


            if len(subfieldA) > 0 :
                #If there are no 930$s and at least one 866$a
                if len(subfieldS) == 0:

                    if len(subfieldA) > 1:
                        myField = record["930"]
                        #Copy 930 fields
                        for i in range(0, len(subfieldA)-1):
                            record.add_field(copy.deepcopy(myField))
                            rowsAdded = rowsAdded + 1
                            
                        #Add the different 866$a
                        allFields = record.get_fields("930")
                        if len(allFields) > len(subfieldA):
                            myRecord = [SysNum, OclcNum, title, subfieldA, subfieldS, "Should be Manually Checked"]
                            onlyFileWriter.writerow(myRecord)
                            changedRecordsWriter.write(record)
                        else:
                            myRecord = [SysNum, OclcNum, title, subfieldA, subfieldS, "Fake CTCC Barcode Added"]
                            onlyFileWriter.writerow(myRecord)

                            for x in range(1, len(allFields)):
                                allFields[x].delete_subfield("5")
                                myBarcode = createBarcode(number)
                                number = number + 1
                                allFields[x].add_subfield("5", myBarcode)

                            for i in range(0, len(allFields)):
                                #allFields[i].add_subfield("s", subfieldA[i])
                                y = len(allFields[i].subfields)-2
                                allFields[i].subfields.insert(y, "s")
                                allFields[i].subfields.insert(y+1, subfieldA[i])
                                
                            changedRecordsWriter.write(record)

                    else:
                        myRecord = [SysNum, OclcNum, title, subfieldA, subfieldS, "Record Changed"]
                        onlyFileWriter.writerow(myRecord)

                        myField = record["930"]
                        y = len(myField.subfields)-2
                        myField.subfields.insert(y, "s")
                        myField.subfields.insert(y+1, subfieldA[0])
                        #myField.add_subfield("s", subfieldA[0])
                        changedRecordsWriter.write(record)

                #If there is a 930$s   
                else:             
                    unchangedRecordsWriter.write(record)
                    myRecord = [SysNum, OclcNum, title, subfieldA, subfieldS, "Unchanged Record"]
                    onlyFileWriter.writerow(myRecord)

                    #Find Records with Coverage Years that don't match (866$a and 930$s)
                    allAIterations = []
                    allSIterations = []
                    findIterationsOfYears(subfieldA, subfieldS, allAIterations, allSIterations)
                    allAIterations = rebuildYearArray(allAIterations)
                    allSIterations = rebuildYearArray(allSIterations)

                    allAIterations = cleanUpArrays(allAIterations)
                    allSIterations = cleanUpArrays(allSIterations)

                    if len(allAIterations) == 0 and len(allSIterations) == 0:
                        myRecord = [SysNum, OclcNum, title, subfieldA, subfieldS, "No Year Info"]
                        csvFileWriter.writerow(myRecord)
                    elif allAIterations == allSIterations:
                        myRecord = [SysNum, OclcNum, title, subfieldA, subfieldS, "Same Coverage"]
                        csvFileWriter.writerow(myRecord)
                    else:
                        myRecord = [SysNum, OclcNum, title, subfieldA, subfieldS, "Different Coverage"]
                        csvFileWriter.writerow(myRecord)

            #If there are no $a and no $s
            elif len(subfieldA) == 0 and len(subfieldS) == 0:
                myRecord = [SysNum, OclcNum, title, subfieldA, subfieldS, "Unchanged Record no coverage info"]
                onlyFileWriter.writerow(myRecord)
                unchangedRecordsWriter.write(record)
            else:
                myRecord = [SysNum, OclcNum, title, subfieldA, subfieldS, "Other unchanged record"]
                onlyFileWriter.writerow(myRecord)
                unchangedRecordsWriter.write(record)
        else:
            deletedRecordsWriter.write(record)
        items = record.get_fields("930")
        finalItemCount = finalItemCount + len(items)

    print("Number of records for " + filename + ": " + str(len(sysNumCountArray)))
    print("Number of original items for " + filename + ": " + str(originalItemCount))
    print("Final number of items for " + filename + ": " + str(finalItemCount))
print("Number of deleted rows: " + str(rowsDeleted))
print("Number of added rows: " + str(rowsAdded))
unchangedRecordsWriter.close()
changedRecordsWriter.close()

