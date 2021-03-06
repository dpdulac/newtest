#!/usr/bin/env python
# coding:utf-8
""":mod: sourceDir
===================================

.. module:: moduleName
   :platform: Unix
   :synopsis: module idea
   :author: duda
   :date: 2021.01
   
"""
from datetime import datetime, timedelta
import os, sys, fnmatch, argparse, logging

logging.basicConfig(level=logging.INFO,
                    format='\x1b[0;34;10m %(levelname)s :: %(lineno)d :: %(module)s :: \x1b[1;37m%(message)s\x1b[0m')
logger = logging.getLogger(__name__)


class readSourceDir:
    def __init__(self, date):
        self.today = datetime.now().strftime("%y%m%d")
        self.year = datetime.now().strftime("%y")
        self.day = datetime.now().strftime("%d")
        self.month = datetime.now().strftime("%m")
        self.yesterday = self.year + self.month + str(int(self.day) - 1)
        self.inputDay = date
        self.pathSourceDir = '/s/prodanim/ta/_exchange/FROM_PMT/_sourcePkg/'
        self.imageFormat = 'jpg'
        self.fileFound = []

    def setInputDay(self, date):
        self.inputDay = date

    def getInputDay(self):
        return self.inputDay

    def getTodayDate(self):
        return self.today

    def setYear(self, year):
        self.year = str(year)

    def getYear(self):
        return self.year

    def setDay(self, day):
        self.day = str(day)

    def getDay(self):
        return self.day

    def setMonth(self, month):
        self.month = str(month)

    def getYesterday(self):
        return self.yesterday

    def setPathSourceDir(self, path):
        self.pathSourceDir = path

    def getPathSourceDir(self):
        return self.pathSourceDir

    def setImageFormat(self, format):
        self.imageFormat = format

    def getImageFormat(self):
        return self.imageFormat

    def setFileFound(self, fileList=[]):
        self.fileFound = fileList

    def getFileFound(self):
        return self.fileFound

    # find the files to display in rv
    def findFile(self):
        # go to the pathSourceDir
        os.chdir(os.path.dirname(self.pathSourceDir))
        # find all the dir corresponding to the good date
        listDir = [f for f in os.listdir('.') if f.find(self.inputDay) >= 0]
        # extract the file
        for dirPath in listDir:
            for root, dirnames, filenames in os.walk(dirPath):
                for filenames in fnmatch.filter(filenames, '*.' + self.imageFormat):
                    self.fileFound.append(self.pathSourceDir + os.path.join(root, filenames))
        return self.fileFound

    # display the images on rv
    def displayRv(self):
        self.findFile()
        stringFile = ''
        for f in self.fileFound:
            stringFile += f + ' '
        stringFile = stringFile[:stringFile.rfind(' ')]
        if stringFile != '':
            os.system('rv ' + stringFile)
        else:
            logger.error('No file found try again!!!')


def argParse():
    # Assign description to the help doc
    parser = argparse.ArgumentParser(description='launch rv with the images from directory which start with a format '
                                                 '%y%m%d (i.e: 201101) the images will be search recursively from the'
                                                 ' root. If no argument the image from the day before current'
                                                 ' day will be processed', add_help=True, epilog=''
                                                 'Example of use: sourceDir -d 210115 -s 5 for 10 of january 2021')
    parser.add_argument('--d', '-d', type=str, help='intput date default is yesterday')
    parser.add_argument('--s', '-s', type=int, default=-1, help='shift the date from current day backward')
    parser.add_argument('--dirPath', '-dirPath', type=str, help='root directory')
    args = parser.parse_args()

    # check and set input day
    inputDate = ''
    if args.d is not None:
        if len(args.d) != 6 or not args.d.isdigit():
            logger.error('wrong format (i.e: sourceDir -d 210115 for 2021 january 15th')
            sys.exit()
        elif not str(args.s).isdigit():
            logger.error('wrong format (i.e: sourceDir -d 210115 -s 2 for 2021 january 13th')
            sys.exit()
        else:
            year = args.d[:2]
            month = args.d[2:4]
            day = args.d[4:]
            inputDate = (datetime(int('20' + year), int(month), int(day)) - timedelta(days=int(args.s))).strftime(
                "%y%m%d")
    else:
        print(args.s)
        # put today date moins shift
        if args.s != -1:
            inputDate = (datetime.today() - timedelta(days=int(args.s))).strftime("%y%m%d")
        # put yesterday date
        else:
            inputDate = (datetime.today() - timedelta(days=1)).strftime("%y%m%d")
    return inputDate


def main():
    date = argParse()
    today = readSourceDir(date)
    today.displayRv()


if __name__ == '__main__':
    main()
