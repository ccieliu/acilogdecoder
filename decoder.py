import logging
import re
import json
import time
import tarfile
import os
import datetime
import hashlib
import xml.etree.ElementTree as ET


class logDecoder(object):
    'The ACI XML log decoder.'
    def __init__(self, srNo='temp'):
        self.srNo = srNo  # Receive SR number

        # Setup a log formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(filename)s[line:%(lineno)d] - %(funcName)s - %(levelname)s : %(message)s")

        # Setup a log console handler and set level/formater
        logConsole = logging.StreamHandler()
        logConsole.setFormatter(formatter)

        # Setup a logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logConsole)
        self.logger.debug("Created a new job for SR: " + str(srNo))

        def _checkAndInitDir(dirItem, srNo):
            '''Check if sr dir exist, if not create them'''
            self.dirLocation = './data/' + dirItem + '/' + srNo + '/'

            if os.path.exists(self.dirLocation):
                # Check the dir if exists
                self.logger.debug(self.dirLocation + " check pass.")
            else:
                try:
                    os.mkdir(self.dirLocation)
                except FileNotFoundError:
                    self.logger.critical("No SR dir found.")
                self.logger.debug(self.dirLocation +
                                  " not exist, created them.")

        # The dirs which required.
        requiredDir = ['logs', 'origin', 'result', 'downloads', 'uploads']

        for dirItem in requiredDir:
            '''Loop all required dirs. and init them'''
            _checkAndInitDir(dirItem=dirItem, srNo=self.srNo)
        # Setup a log file handler and set level/formater
        logFile = logging.FileHandler(os.getcwd()+"/data/logs/" + self.srNo + "/runtime.log")
        logFile.setFormatter(formatter)
        self.logger.addHandler(logFile)

    def actionsTarFile(self, originFileName, actionName):
        '''
        Actions about tar/tar.gz/tgz files. include getnames or unzip.
        actionName can be 'getnames' or 'unzip' or 'zip'
        '''
        originFilePath = "./data/uploads/" + self.srNo + '/'+originFileName

        originFileHash = hashlib.md5()
        try:
            originFileHash.update(str(os.path.getsize(originFilePath)).encode())
        except FileNotFoundError:
            self.logger.critical("Not found originFilePath")
        self.originFileHash = originFileHash.hexdigest()[:6]

        self.targetPath = "./data/origin/" + self.srNo + "/" + \
            self.originFileHash + "/"
        self.logger.debug('Take action: '+actionName+' at: '+self.targetPath)

        def __actions(actionName, targetPath=self.targetPath):
            '''Two action for files."getnames" & "unzip" '''
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
                tar = tarfile.open(originFilePath, "r:gz")
            except FileExistsError as e:
                self.logger.error("File unzip error: " + str(e))
            except FileNotFoundError:
                self.logger.critical("Not found originFilePath")
            return(__actions(actionName, self.targetPath))
        elif (originFileName.endswith("tar")):
            '''The actions for 'tar' files.'''
            try:
                tar = tarfile.open(originFilePath, "r:")
            except FileExistsError as e:
                self.logger.error("File unzip error: " + str(e))
            return(__actions(actionName, self.targetPath))
        else:
            self.logger.error("This type file do not support as for now.")

    def compressResultDir(self):
        '''Compress all the SR file in result downloads dir'''
        tarCompressDir = "./data/result/" + self.srNo + '/' +self.originFileHash
        tarTargetFile = "./data/downloads/" + self.srNo + \
            datetime.datetime.now().strftime("/%Y%m%d_%H_%M_%S_%f-SR_")+self.srNo + ".tgz"

        resultTarFile = tarfile.open(tarTargetFile, "w:gz")
        # Add tarCompressDir into the tar.gz file.
        resultTarFile.add(
            tarCompressDir, arcname=os.path.basename(tarCompressDir))
        resultTarFile.close()
        self.logger.debug("SR: "+str(self.srNo)+ ' Compress output: ' + tarTargetFile)
        return(tarTargetFile.lstrip("."))  # Return the path of compressed file.

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
            # "./data/origin/" + self.srNo + "/" + xmlFileName, parser=ET.XMLParser(encoding='iso-8859-5'))
            self.targetPath + xmlFileName, parser=ET.XMLParser(encoding='iso-8859-5'))
        # Get root from xml file
        self.root = self.tree.getroot()
        outputFile = "./data/result/" + self.srNo + '/' + self.originFileHash + '/' +\
            datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S_%f_SR-") + \
            self.srNo + '-' + xmlFileName + ".txt"
        try:
            os.mkdir("./data/result/" + self.srNo + '/' + self.originFileHash + '/')
        except FileExistsError:
            pass
        resultFile = open(outputFile, mode='w', encoding='utf-8')
        try:
            for child in self.root:  # Loop all tree from root
                # All log line must start from 'created', and formated the timezone Eg."2019-03-15 09:12:00.005 GMT+08:00"
                resultStr = child.attrib['created'].split(
                    "+")[0].replace('T', " ")
                for attribItem in attribList:  # Loop attribList
                    # Append item which in the attriblist
                    resultStr = resultStr + splitStr + child.attrib[attribItem]
                resultFile.write(resultStr+'\n')  # Writeline into the file
                # print(resultStr)
            resultFile.close()  # Secure close the file.
            self.logger.debug("Output result file at: "+str(outputFile))
            return(outputFile)  # Return the path of the result file.
        except KeyError as e:
            self.logger.error("There isn't a key named ->" +
                              str(e) + " in file: " + xmlFileName + ", please review your attrib list.")


if __name__ == "__main__":
    myattribList = ['severity', 'code', 'affected', 'changeSet', 'descr']
    myoriginFileName = 'eventRecord1.tar'
    Client = logDecoder(srNo="000")


    Client.actionsTarFile(originFileName=myoriginFileName,
                          actionName='unzip')
    for i in Client.actionsTarFile(originFileName=myoriginFileName, actionName='getnames'):
        Client.returnLineResult(xmlFileName=i, attribList=myattribList)
    Client.compressResultDir()
