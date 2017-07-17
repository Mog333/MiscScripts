import os
from shutil import copyfile
import shutil
import re
import sys
import subprocess
import numpy as np

reAlphabet = re.compile("[a-zA-Z]")

def moveFoldersUp(baseFolder, folderToDelete):
    for f in os.listdir(baseFolder):
        for f2 in os.listdir(baseFolder + "/" + f + folderToDelete):
            shutil.move(baseFolder + "/" + f + "/" + folderToDelete +"/"+ f2, baseFolder + "/" +f)
        shutil.rmtree(baseFolder + "/" + f + "/" + folderToDelete)

def getFilenameFromPath(pathToFile):
    lastSlash = pathToFile.rindex("/")
    return pathToFile[lastSlash + 1:]

def getFilenameWithoutExtension(filename):
    extensionStart = filename.rindex(".")
    return filename[:extensionStart]

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

def getBestEpochOfResults(resultsTuple):
    '''
    Arguments:
        resultsTuple:   tuple containing 3 elements: 
                        x data array, y data array, and optional std dev data

    Returns:
        Tuple (x element, y element)

    Description:
        Returns a tuple that corresponds to the max y element and corresponding x element

    '''

    bestRewardIndex   = np.argmax(res[1])
    bestReward        = res[1][bestRewardIndex]
    bestEpoch         = res[0][bestRewardIndex]

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

def getBestProjectResults(directory, taskNumber = 0, resultsCollectionFunction = getResultsFromTaskFile):
    '''
    Arguments:
        directory: (string)
            starting directory

        resultsCollectionFunction: (function similar to getResultsFromTaskFile above.)
            use lambda function to use the getResultsFromTaskFile with different parameters than default

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
                fullPath          = root + "/" + file
                res               = resultsCollectionFunction(fullPath)
                
                resultsDict[file] = (bestEpoch, bestReward)

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

def writeAveragedDataFileOverMultipleSeeds(directory, resultsFilesNames, resultsCollectionFunction = getResultsFromTaskFile):
    '''
    Arguments:
        directory: (string)
            directory containing seed folders, each a project directory
            Each seed folder has format seed_x

        resultsFilesNames: (string or list of string)
            A string or list of strings that represent a task file that should be present in each seed folder
        
        resultsCollectionFunction: (function similar to getResultsFromTaskFile above.)
            use lambda function to use the getResultsFromTaskFile with different parameters than default


    Description:
        For each results task file given in resultsFilesNames
        Computes data averaged over multiple seeds then
        writes it to a file with the same name as the results file with the prefix "averaged_"
    '''
    
    if type(resultsFilesNames) == str:
        resultsFilesNames = [resultsFilesNames]

    contents    = os.listdir(directory)
    seedFolders = []
    
    for c in contents:
        if "seed_" in c:
            seedFolders.append(c)

    seedFolders = sorted(seedFolders)

    for resultsFileName in resultsFilesNames:
        allTaskResults = []

        for seedFolder in seedFolders:
            taskFilename = directory + "/" + seedFolder + "/" + resultsFileName
            taskResults = resultsCollectionFunction(taskFilename)
            allTaskResults.append(taskResults)

        averagedData = computeAveragedDataOverMultipleSeeds(allTaskResults)
        averagedFilename = directory + "/averaged_" + resultsFileName

        writeDataToFile(averagedFilename, allTaskResults[0][0], averagedData[0], averagedData[1])



def computeAveragedDataOverMultipleSeeds(seedData):
    '''
    Arguments:
        seedData: (array of array of numpy arrays)
            number of arrays = number of seeds, each contains 3 numpy arrays, for x,y,stddev data - we only need y data for this
            each numpy array should have the same length
            

    Returns:
        returns an array of two numpy arrays
            first one is the averaged data, second is the std dev 

    Description:
        Creates numpy arrays to hold averaged data and std deviation of data
    '''


    # print seedData
    numSeeds = len(seedData)
    numDataPoints = len(seedData[0])

    yData = np.array(seedData[0][1])
    for seedIndex in xrange(1, numSeeds):
        yData = np.vstack((yData, seedData[seedIndex][1]))

    means   = np.mean(yData, axis = 0)
    stdDevs = np.std(yData, axis = 0, ddof = 1)

    # print(numDataPoints)
    # print(len(means))
    # print(len(stdDevs))
    # print means
    # print stdDevs

    return np.array([means, stdDevs])
    





def computeAverageOverMultipleSeeds(directory, sumData = False, resultsCollectionFunction = getResultsFromTaskFile):
    '''
    Arguments:
        directory: (string)
            directory containing seed folders, each a project directory
            Each seed folder has format seed_x
            Each seed folder has the same number of tasks of format task_y_results.csv

        resultsCollectionFunction: (function similar to getResultsFromTaskFile above.)
            use lambda function to use the getResultsFromTaskFile with different parameters than default


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
            res = resultsCollectionFunction(resPath)

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
            resultsStdDev[index]   = np.std( resultsData[index], dd0f = 1)# / np.sqrt(len(resultsData[index]))

        # print resultsAveraged
        # print resultsStdDev

        # for i in xrange(numDatapoints):
        #     print str(resultsAveraged[i]) + " std: " + str(resultsStdDev[i])

        masterResults.append((np.array(epochsList), resultsAveraged, resultsStdDev))

    return masterResults

def createSummedDataFile(sourceFile, resultsCollectionFunction = getResultsFromTaskFile):
    '''
    Arguments:
        sourceFile:   (string)
            file to collect experiment data from

        resultsCollectionFunction:  (function)
                Function takes one argument: (string) which is a path to a results file
                returns a list of three lists with x,y,stddev data
                example:
                    resultsCollectionFunction = lambda f: getResultsFromTaskFile(f, 0, 3, -1)

    Description:
        reads the x/y data of a results file in columns, 
        computes the summed data ( each y value is the sum of all previous y values),
        writes the resulting summed data to a file
            file name is sourceFile with _Summed suffix before file extension
    '''

    startFilenameIndex  = sourceFile.rindex("/")
    sourceFileDirectory = sourceFile[0: startFilenameIndex + 1 ]
    sourceFilename      = sourceFile[startFilenameIndex + 1 : ]
    sourceExtensionIndex= sourceFilename.rindex(".")
    destinationFilename = sourceFileDirectory + sourceFilename[0:sourceExtensionIndex] + "_Summed" + sourceFilename[sourceExtensionIndex : ]
    
    results = resultsCollectionFunction(sourceFile)
    results[1] = computeSummedData(results[1])
    writeDataToFile(destinationFilename, results[0], results[1], None)


def findResultsFiles(directory, condition = lambda c: (c.startswith("task_") and c.endswith(".csv") and "results" in c)):
    '''
    Arguments:
        directory:  (string)
            a directory containing result files for multiple tasks
            results files have form: task_x_results*.csv
            where * represents a wild card for suffixed like "_Summed"

    Returns:
        Returns a list of strings for each task result file 
    '''

    contents = os.listdir(directory)
    return sorted([c for c in contents if condition(c)])

def findAllExperimentSeedBaseFoldersUnderDirectory(directory):
    '''
    Arguments:
        directory:  (string)
            a directory path within which are projects that have seed folders

    Returns:
        Returns a list of subdirectories which contain seed folders of format "seed_*"
    '''
    multiseedProjectBaseFolders = []
    for root, subdirs, files in os.walk(directory):
        for subdir in subdirs:
            currentPath = root + "/" + subdir
            contents = os.listdir(currentPath)
            hasSeedFolders = [True for c in contents if (c.startswith("seed_") and os.path.isdir(currentPath + "/" + c))]
            if True in hasSeedFolders:
                multiseedProjectBaseFolders.append(currentPath)

    return multiseedProjectBaseFolders

def createAveragedResultsFilesForDirectory(directory, resultFileNames = ["task_0_results.csv"], resultsCollectionFunction = getResultsFromTaskFile):
    '''
    Arguments:
        directory:  (string)
            a directory path within which are projects that have seed folders

        resultsFilesNames: (string or list of string)
            A string or list of strings that represent a task file that should be present in each seed folder
        
        resultsCollectionFunction: (function similar to getResultsFromTaskFile above.)
            use lambda function to use the getResultsFromTaskFile with different parameters than default


    Description:
        Writes a averaged file for/in every directory found that has seed folders 
    '''
    experimentBaseDirectories = findAllExperimentSeedBaseFoldersUnderDirectory(directory)
    print(experimentBaseDirectories)
    for experimentBase in experimentBaseDirectories:
        writeAveragedDataFileOverMultipleSeeds(experimentBase, resultFileNames, resultsCollectionFunction)






def calculateBestEpochForMultitaskExperiment(experimentDirectory, numBestEpochsToReturn = 1, resultsCollectionFunction = getResultsFromTaskFile, taskWeightingArray = None):
    contents = os.listdir(experimentDirectory)
    taskFiles = sorted([file for file in contents if ("task_" in file and ".csv" in file and ".~" not in file)])
    numTasks = len(taskFiles)

    if taskWeightingArray == None:
        taskWeightingArray = [1] * numTasks
    elif len(taskWeightingArray) != numTasks:
        print("TaskWeightingArray Paramater has length different than expected. Num weights: " + str(len(taskWeightingArray)) + " Num tasks: " + str(numTasks))
        return

    allTasksInfo = {}

    currentTaskNumber = 0
    for taskFile in taskFiles:
        allTasksInfo[currentTaskNumber] = {}
        taskFilePath = experimentDirectory + "/" + taskFile
        results = resultsCollectionFunction(taskFilePath)

        bestEpoch,bestAverageReward = getBestEpochOfResults(results)
        
        allTasksInfo[currentTaskNumber]["resultsTuple"] = results
        allTasksInfo[currentTaskNumber]["bestAverageReward"] = bestAverageReward
        allTasksInfo[currentTaskNumber]["bestEpoch"] = bestEpoch        
        allTasksInfo[currentTaskNumber]["numEpochs"] = len(results[0])
        currentTaskNumber += 1

    numEpochs = allTasksInfo[0]["numEpochs"]
    for taskInfoKey in allTasksInfo:
        if allTasksInfo[taskInfoKey]["numEpochs"] != numEpochs:
            print("Two tasks have different number of epochs!")
            return

    rewardWeightedData = []
    for rowIndex in xrange(numEpochs):
        currentEpochRewardWeighting = 0
        for taskIndex in xrange(numTasks):
            currentEpochRewardWeighting += taskWeightingArray[taskIndex] * (allTasksInfo[taskIndex]["resultsTuple"][1][rowIndex] / allTasksInfo[taskIndex]["bestAverageReward"])
        print currentEpochRewardWeighting
        rewardWeightedData.append([allTasksInfo[taskIndex]["resultsTuple"][0][rowIndex], currentEpochRewardWeighting])

    rewardWeightedData.sort(key = lambda element: element[1])
    bestEpochAndReward = rewardWeightedData[numEpochs - numBestEpochsToReturn:]

    returnDict = {}
    returnDict["bestPerTaskEpochData"] = []
    returnDict["bestMultitaskEpochData"] = bestEpochAndReward
    
    for taskIndex in xrange(numTasks):
        returnDict["bestPerTaskEpochData"].append([ allTasksInfo[taskIndex]["bestEpoch"], allTasksInfo[taskIndex]["bestAverageReward"] ])

    return returnDict








def function1():
    '''
    Create averaged files for both normal and summed data over multiple seeds
    two typed of seeded folders
        dqn baselines with full and min action sets containing 1 task
        4 task transfer experiments

    summed/normal use different result collection function as summed has different data column structure
    '''

    resultsCollectionFunction        = lambda f: getResultsFromTaskFile(f, 0, 3, -1)
    resultsCollectionFunctionSummed  = lambda f: getResultsFromTaskFile(f, 0, 1, -1)

    result1TaskFileNames         = ["task_0_results.csv"]
    result1TaskFileNamesSummed   = ["task_0_results_Summed.csv"]

    result4TaskFileNames         = ["task_0_results.csv", "task_1_results.csv", "task_2_results.csv", "task_3_results.csv"]
    result4TaskFileNamesSummed   = ["task_0_results_Summed.csv", "task_1_results_Summed.csv", "task_2_results_Summed.csv", "task_3_results_Summed.csv"]


    createAveragedResultsFilesForDirectory("/home/robert/Desktop/Research/DTQN/compiledResults/dqnFullBaselineResult", result1TaskFileNames, resultsCollectionFunction)
    createAveragedResultsFilesForDirectory("/home/robert/Desktop/Research/DTQN/compiledResults/dqnFullBaselineResult", result1TaskFileNamesSummed, resultsCollectionFunctionSummed)

    createAveragedResultsFilesForDirectory("/home/robert/Desktop/Research/DTQN/compiledResults/dqnMinBaselineResult", result1TaskFileNames, resultsCollectionFunction)
    createAveragedResultsFilesForDirectory("/home/robert/Desktop/Research/DTQN/compiledResults/dqnMinBaselineResult", result1TaskFileNamesSummed, resultsCollectionFunctionSummed)


    createAveragedResultsFilesForDirectory("/home/robert/Desktop/Research/DTQN/compiledResults/transferMultigameResult", result4TaskFileNames, resultsCollectionFunction)
    createAveragedResultsFilesForDirectory("/home/robert/Desktop/Research/DTQN/compiledResults/transferMultigameResult", result4TaskFileNamesSummed, resultsCollectionFunctionSummed)

    createAveragedResultsFilesForDirectory("/home/robert/Desktop/Research/DTQN/compiledResults/transferBaselinesDisjoint", result4TaskFileNames, resultsCollectionFunction)
    createAveragedResultsFilesForDirectory("/home/robert/Desktop/Research/DTQN/compiledResults/transferBaselinesDisjoint", result4TaskFileNamesSummed, resultsCollectionFunctionSummed)




def function2():
    resultsCollectionFunction = lambda f: getResultsFromTaskFile(f, 0, 3, -1)
    # computeAverageOverMultipleSeeds("testSeedAvg", resultsFunction= resultsCollectionFunction)
    d = calculateBestEpochForMultitaskExperiment("/home/robpost/Desktop/Research/MiscScripts/test/multitaskDataTest/", numBestEpochsToReturn = 3, resultsCollectionFunction = resultsCollectionFunction, taskWeightingArray = [1,1,50,1])
    print(d["bestPerTaskEpochData"])
    print("\n\n\n")
    print(d["bestMultitaskEpochData"])


def function3():
    resultsCollectionFunction        = lambda f: getResultsFromTaskFile(f, 0, 3, -1)
    resultsCollectionFunctionSummed  = lambda f: getResultsFromTaskFile(f, 0, 1, -1)

    baseFolder = "/home/robert/Desktop/Research/MultiGameResults/20EpochResultsOnly/"
    experimentDirectories = findAllExperimentSeedBaseFoldersUnderDirectory(baseFolder)

    result4TaskFileNames         = ["task_0_results.csv", "task_1_results.csv", "task_2_results.csv", "task_3_results.csv"]
    result4TaskFileNamesSummed   = ["task_0_results_Summed.csv", "task_1_results_Summed.csv", "task_2_results_Summed.csv", "task_3_results_Summed.csv"]

    #Creates all summed data files for every result file

    for experimentDirectory in experimentDirectories:
        seedFolders = [x for x in os.listdir(experimentDirectory) if "seed" in x]

        for seed in seedFolders:
            currentDirectory = experimentDirectory + "/" + seed
            resultFiles = findResultsFiles(currentDirectory)

            for resultFile in resultFiles:
                fullPath = currentDirectory + "/" + resultFile
                # print(fullPath)
                createSummedDataFile(fullPath , resultsCollectionFunction)

    #Then creates the average over the task files and the average over the summed task files 
    createAveragedResultsFilesForDirectory(baseFolder, result4TaskFileNames, resultsCollectionFunction)
    createAveragedResultsFilesForDirectory(baseFolder, result4TaskFileNamesSummed, resultsCollectionFunctionSummed)



def main(args):
    resultsCollectionFunction        = lambda f: getResultsFromTaskFile(f, 0, 3, -1)
    resultsCollectionFunctionSummed  = lambda f: getResultsFromTaskFile(f, 0, 1, -1)

    # function1()
    function3()
    
    # condition       = lambda c: (c.startswith("task_") and c.endswith(".csv") and "results" in c and "Summed" not in c)
    # conditionSummed = lambda c: (c.startswith("task_") and c.endswith(".csv") and "results" in c and "Summed" in c)
    
    # resultFileNames = findResultsFiles("/home/robert/Desktop/Research/DTQN/compiledResults/transferMultigameResult/enduro^pong^gopher^space_invaders/DQNNet/seed_1", condition)
    # resultFileNamesSummed = findResultsFiles("test/seed_1/", conditionSummed)

    # createSummedDataFile(args[0], resultsCollectionFunction)
    # computeAverageOverMultipleSeeds("testSeedAvg", resultsCollectionFunction= resultsCollectionFunction)

    # writeAveragedDataFileOverMultipleSeeds("test/", resultFileNames, resultsCollectionFunction)
    # writeAveragedDataFileOverMultipleSeeds("test/", resultFileNamesSummed, resultsCollectionFunctionSummed)

    # projectSeedDirs = createAveragedResultsFilesForDirectory("/home/robert/Desktop/Research/DTQN/compiledResults/transferMultigameResult")
    # for i in projectSeedDirs:
        # print i 

if __name__ == "__main__":
    main(sys.argv[1:])



