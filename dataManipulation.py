import os
from shutil import copyfile
import shutil
import re
import sys
import subprocess
import numpy as np

reAlphabet = re.compile("[a-zA-Z]")


def getResultsFromTaskFile(filename, xColumn = 0, yColumn = 1, stdDevColumn = 2, dataDelimiter = ','):
    '''
    Arguments:
        filename:       (string)    name of file to load

    Optional Arguments:
        xColumn:        (int  Default: 0)   column index in file for x data
        yColumn:        (int  Default: 1)   column index in file for y data
        stdDevColumn:   (int  Default: 2)   column index in file for stdDev of y data
            If stdDevColumn is negative its ignored and no stdDev data is loaded 
        dataDelimiter:  (char Default: ,)   Character separating columns in file

    Returns:
        Tuple containing 3 numpy arrays for x, y, stdDev Data
        If stdDevColumn is negative the third element in the tuple is None

    Exceptions:
        IOError:    Error reading from file
        IndexError: Error reading data from a column that doesn't exist

    Description:
        Reads in a task file that consists of columns of data
        2 columns mandatory x / y, and optional 3rd column for std dev

        Ignores all lines with alphabet characters in it. ie: headers
    '''


    if not os.path.exists(filename):
        raise IOError("Couldnt load file:" + str(filename))

    resFile = open(filename, 'r')

    rewards       = np.zeros(0)
    epochs        = np.zeros(0)
    
    if stdDevColumn < 0:
        rewardStdDevs = None
    else:
        rewardStdDevs = np.zeros(0)

    line = resFile.readline()

    while  line != "":
        if line == '\n' or line == '':
            continue

        #Lines in a data file cant contain alphabet characters - skip this line
        if reAlphabet.match(line) == None:
            contents = line.split(dataDelimiter)

            try:
                epochs  = np.append(epochs, float(contents[xColumn].strip()))
                rewards = np.append(rewards, float(contents[yColumn].strip()))

                if stdDevColumn > -1:
                    rewardStdDevs = np.append(rewardStdDevs, float(contents[stdDevColumn].strip()))
            except IndexError:
                raise IndexError("Index error: data couldnt be loaded from the given file with the provided format")

        line = resFile.readline()

    resFile.close()
 
    return [epochs, rewards, rewardStdDevs]



def computeSummedData(data):
    '''
    Arguments:
        data:   (numpy list of floats)

    Returns:
        a numpy array of the same dimensions as the input 
        inwhich each element is the sum of the previous elements

    '''

    newData = np.empty_like(data)
    newData[0] = data[0]
    for i in xrange(1,len(data)):
        newData[i] = newData[i - 1] + data[i]
    return newData


def divideDataElementsByFactor(data, factor):
    '''
    Arguments:
        data:   (numpy list of floats)

        factor: (float)
            float to divide each element in data by

    Returns:
        a numpy array of the same dimensions as the input 
        inwhich each element is divided by a factor

    '''
    newData = np.empty_like(data)

    for index in xrange(len(data)):
        newData[index] = data[index] / factor

    return newData



def getBestEpochOfResults(resultsTuple):
    '''
    Arguments:
        resultsTuple:   tuple containing 3 elements: 
                        x data array, y data array, and optional std dev data

    Returns:
        Tuple (x element, y element)

    Exceptions:
        None

    Description:
        Returns a tuple that corresponds to the max y element / x element

    '''

    bestEpoch  = resultsTuple[0][0]
    bestReward = resultsTuple[1][0]

    numElements = len(resultsTuple[0])
    for index in xrange(numElements):
        currentReward = resultsTuple[1][index]
        if currentReward > bestReward:
            bestReward = currentReward
            bestEpoch = resultsTuple[0][index]

    return (bestEpoch, bestReward)


def getALEGameList(baseRomPath, removeExtension = True):
    '''
    Arguments:
        baseRomPath:    (string)
            directory string that contains all the ALE roms

        removeExtension:(string) Default=True
            boolean to remove the ".bin" extension from the rom or not

    Description:
        returns a list of strings of ALE roms with the ".bin " extension removed or not
    '''

    contents = os.listdir(baseRomPath)
    gameList = []
    for item in contents:
        if item.endswith(".bin"):
            if removeExtension:
                item = item[0:-4]

            gameList.append(item)

    return gameList



def getHighestNetworkFileEpoch(projectDirectory):
    '''
    Arguments:
        projectDirectory: (string)
            directory string of location of project

    Returns:
        returns an integer for the highest network file number in the directory or None

    Description:
        returns the epoch number of the highest network file in the directory

    '''
    contents = os.listdir(projectDirectory)
    networks = [c for c in contents if "network" in c and ".pkl" in c]

    if len(networks) == 0:
        return None

    def getNumFromNetworkString(s):
        return s[s.index('_') + 1 : s.index('.')]

    highestNum = getNumFromNetworkString(networks[0])

    for network in networks:
        num = getNumFromNetworkString(network)
        if num > highestNum:
            highestNum = num

    return highestNum



def getBestProjectResults(directory, taskNumber = 0, resultsFunction = getResultsFromTaskFile):
    '''
    Arguments:
        directory: (string)
            starting directory

        resultsFunction: (function similar to getResultsFromTaskFile above.)
            use lambda function to use the getResultsFromTaskfile with different parameters than default

    Returns:
        string containing the best epoch / result for all the experiments under the given directory
        but only considering the one task number (experiments could contain multiple results files)

    Description:
        Walks through the directory finding every experiment (folder containing .pbs file or .json parameters file)
        collects the best epoch / result for each project and returns a string with these elements

    '''

    resultsDict = {}
    for root, subdirs, files in os.walk(directory):
        for file in files:
            if file == "task_" + str(taskNumber) + "_results.csv":
                #found a project directory

                fullPath = root + "/" + file
                res = resultsFunction(fullPath)
                res = getBestEpochOfResults(res)
                resultsDict[file] = res

    resultString = ""
    for key in sorted(resultsDict.keys()):
        resultString += '{:<40}'.format(str(key) + ",") 
        resultString += str(gameDict[key][1]) + " at epoch: " + str(gameDict[key][0]) 
    return resultString







def copyCompiledResultsFolder(directory, outputPath, justPrint = False):
    '''
    Arguments:
        directory: (string)
            directory where to start finding project directories

        outputPath: (string)
            directory to copy projects to

    Description:
        Walks through the given directory finding all projects
        each project and the folders its under is copied to the outputPath
        copies the all task result files

    '''
    resFiles = []
    for root, subdirs, files in os.walk(directory):
        for file in files:
            if ('result' in file and file.endswith(".csv")):
                fullResultsPath = root + "/" + file
                endOffullResultsPath = fullResultsPath.replace(directory, "")
                resFiles.append(endOffullResultsPath)

    for file in resFiles:
        newPath = outputPath + "/" + file[0:file.rfind("/")]

        print "file:\t"+file
        print "newpath:\t" + newPath

        if not os.path.isdir(newPath):
            os.makedirs(newPath)
        fileToCopy = directory + "/" + file
        newFilename = outputPath + "/" + file
        print "filetocopy:\t"+fileToCopy
        print "newfilename:\t"+newFilename

        if not justPrint:
            copyfile(fileToCopy, newFilename)









def computeAverageOverMultipleSeeds(directory, sumData = False, resultsFunction = getResultsFromTaskFile):
    '''
    Arguments:
        directory: (string)
            directory containing seed folders, each a project directory
            Each seed folder has format seed_x
            Each seed folder has the same number of tasks of format task_y_results.csv

        resultsFunction: (function similar to getResultsFromTaskFile above.)
            use lambda function to use the getResultsFromTaskfile with different parameters than default


    Returns:
        returns an numpy array of numpy arrays each with two inner arrays
        number of arrays = number of tasks
        each task has 2 inner arrays one for results one for std of that result
        
        ex:
                task 1                      task 2  ....
        [
            [[r1,r2,r3],[s1,s2,s3]],  [[r1, r2, r3], [s1, s2, s3]
        ]                 ]

    Description:
        Creates numpy arrays to hold averaged data over multiple seeds
        Assumes each seed has the same number of tasks
    '''
    
    contents = os.listdir(directory)

    seedFolders = []
    taskFiles = []
    for c in contents:
        if "seed_" in c:
            seedFolders.append(c)

    seedFolders = sorted(seedFolders)

    for item in os.listdir(directory + "/" + seedFolders[0]):
        if "results" in item and ".csv" in item:
            taskFiles.append(item)

    taskFiles = sorted(taskFiles)

    numSeeds = len(seedFolders)
    numTasks = len(taskFiles)

    masterResults = []

    for taskFile in taskFiles:
        seedResults = []
        
        numDatapoints = 0
        for seedFolder in seedFolders:
            resPath = directory + "/" + seedFolder + "/" + taskFile
            res = resultsFunction(resPath)

            if sumData:
                res[1] = computeSummedData(res[1])

            seedResults.append(res)
            epochsList = res[0]
            if numDatapoints < len(res[1]):
                numDatapoints = len(res[1])

        resultsData = []
        for count in xrange(numDatapoints):
            resultsData.append(np.zeros(0))
            for r in seedResults:
                if count < len(r[1]):
                    resultsData[count] = np.append(resultsData[count],r[1][count])


        resultsAveraged = np.zeros(numDatapoints)
        resultsStdDev   = np.zeros(numDatapoints)

        for index in xrange(numDatapoints):
            resultsAveraged[index] = np.mean(resultsData[index])
            resultsStdDev[index]   = np.std( resultsData[index])# / np.sqrt(len(resultsData[index]))

        # print resultsAveraged
        # print resultsStdDev

        # for i in xrange(numDatapoints):
        #     print str(resultsAveraged[i]) + " std: " + str(resultsStdDev[i])

        masterResults.append((np.array(epochsList), resultsAveraged, resultsStdDev))

    return masterResults


def writeDataToFile(filename, xData, yData, stdDevData, delimiter = ','):
    '''
    Arguments:
        filename:   (string)
            file to write the data to
        
        xData:      (numpy list of floats)
        yData:      (numpy list of floats)
        stdDevData: (numpy list of floats or None)
        delimiter:  (character)
            character separating data on a single line

    Description:
        writes the x/y data and optionally the stdDevData to a file line by line
    '''


    f = open(filename, 'w')
    
    if stdDevData != None:
        yDelimiter = delimiter
    else:
        yDelimiter = ""

    for index in xrange(len(xData)):

        line = '{:<10}'.format(str(xData[index]) + delimiter)
        line += '{:<25}'.format(str(yData[index]) + delimiter)

        if stdDevData != None:
            line += '{:<25}'.format(str(stdDevData[index]))

        line += "\n"

        f.write(line)


    f.close()



def main():
    resultCollectionFunction = lambda f: getResultsFromTaskFile(f, 0, 3, -1)
    computeAverageOverMultipleSeeds("testSeedAvg", resultsFunction= resultCollectionFunction)






if __name__ == "__main__":
    main()



