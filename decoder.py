import logging
import re
import json
import time
import tarfile
import os
import datetime
import xml.etree.ElementTree as ET


class decoder(object):
    def __init__(self, srNo):
        self.srNo = srNo  # Receive SR number

        # Setup a log formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(filename)s[line:%(lineno)d] - %(funcName)s - %(levelname)s : %(message)s")

        # Setup a log file handler and set level/formater
        logFile = logging.FileHandler("./logs/" + self.srNo + "/runtime.log")
        logFile.setFormatter(formatter)
        # Setup a log console handler and set level/formater
        logConsole = logging.StreamHandler()
        logConsole.setFormatter(formatter)

        # Setup a logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logFile)
        self.logger.addHandler(logConsole)

        def _checkAndInitDir(dirItem, srNo):
            '''Check if sr dir exist, if not create them'''
            self.dirLocation = './' + dirItem + '/' + srNo + '/'

            if os.path.exists(self.dirLocation):
                # Check the dir if exists
                self.logger.debug(self.dirLocation + " check pass.")
            else:
                os.mkdir(self.dirLocation)
                self.logger.debug(self.dirLocation +
                                  " not exist, created them.")

        # The dirs which required.
        requiredDir = ['logs', 'origin', 'result', 'downloads', 'uploads']

        for dirItem in requiredDir:
            '''Loop all required dirs. and init them'''
            _checkAndInitDir(dirItem=dirItem, srNo=self.srNo)

    def actionsTarFile(self, originFileName, actionName):
        '''
        Actions about tar/tar.gz/tgz files. include getnames or unzip.
        actionName can be 'getnames' or 'unzip' or 'zip'
        '''
        originFileName = "./uploads/" + self.srNo + '/'+originFileName
        targetPath = "./origin/" + self.srNo + "/"

        def __actions(actionName, targetPath=targetPath):
            '''Two action for files.'''
            if actionName == 'getnames':
                # Return a list for zip file.
                self.logger.debug(
                    "Return tar name list: " + str(tar.getnames()))
                return(tar.getnames())
            elif (actionName == 'unzip'):
                # If the action name is 'unzip' and there was no path for unzip. the function will rais a exception.
                tar.extractall(path=targetPath)
                return True
            else:
                # Raise a exception for customer. because there was no targetPath but have a 'unzip' action.
                self.logger.error('Action unknow.')
                raise Exception('Action unknow.')
            tar.close()

        if (originFileName.endswith("tar.gz") or originFileName.endswith("tgz")):
            '''The actions for 'tgz/tar.gz' fils'''
            try:
                tar = tarfile.open(originFileName, "r:gz")
            except FileExistsError as e:
                self.logger.error("File unzip error: " + str(e))
            return(__actions(actionName, targetPath))
        elif (originFileName.endswith("tar")):
            '''The actions for 'tar' files.'''
            try:
                tar = tarfile.open(originFileName, "r:")
            except FileExistsError as e:
                self.logger.error("File unzip error: " + str(e))
            return(__actions(actionName, targetPath))
        else:
            self.logger.error("This type file do not support as for now.")

    def compressResultDir(self):
        '''Compress all the SR file in result downloads dir'''
        tarCompressDir = "./result/" + self.srNo
        tarTargetFile = "./downloads/" + self.srNo + \
            datetime.datetime.now().strftime("/%Y%m%d_%H_%M_%S_%f-SR_")+self.srNo + ".tgz"

        resultTarFile = tarfile.open(tarTargetFile, "w:gz")
        # Add tarCompressDir into the tar.gz file.
        resultTarFile.add(
            tarCompressDir, arcname=os.path.basename(tarCompressDir))
        resultTarFile.close()
        return(tarTargetFile)  # Return the path of compressed file.

    def returnLogKeys(self):
        '''Return all log attribute keys.'''
        return(list(self.root[0].attrib))

    def returnLineResult(self, xmlFileName, attribList, splitStr=' '):
        '''Return Line Results and write into a output file.
        Open/Create the resuleFile
        :attribList order is very IMPORTANT for log output. :
        '''

        # Parse the xml file, using iso-8859-5.
        self.tree = ET.parse(
            "./origin/" + self.srNo + "/" + xmlFileName, parser=ET.XMLParser(encoding='iso-8859-5'))
        # Get root from xml file
        self.root = self.tree.getroot()
        outputFile = "./result/" + self.srNo + "/" + \
            datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S_%f-SR_")+self.srNo + ".txt"
        resultFile = open(outputFile, mode='w', encoding='utf-8')
        try:
            for child in self.root:  # Loop all tree from root
                # All log line must start from 'created', and formated the timezone Eg."2019-03-15 09:12:00.005 GMT+08:00"
                resultStr = child.attrib['created'].split(
                    "+")[0].replace('T', " ") + ' GMT +'+child.attrib['created'].split("+")[1]
                for attribItem in attribList:  # Loop attribList
                    # Append item which in the attriblist
                    resultStr = resultStr + splitStr + child.attrib[attribItem]
                resultFile.write(resultStr+'\n')  # Writeline into the file
                # print(resultStr)
            resultFile.close()  # Secure close the file.
            return(resultFile)  # Return the path of the result file.
        except KeyError as e:
            self.logger.error("There isn't a key named ->" +
                              str(e) + ", please review your attrib list.")


if __name__ == "__main__":
    myattribList = ['severity', 'code', 'affected', 'changeSet', 'descr']
    myoriginFileName = 'unexpected-leafdown.tgz'
    myxmlFileName = "eventRecord.xml"

    Client = decoder(srNo="123")
    Client.returnLineResult(
        xmlFileName="faultRecord.xml_with_encode_issue", attribList=myattribList)
