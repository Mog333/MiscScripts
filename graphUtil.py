from pylab import *
import matplotlib.pyplot as plt
import re
import os
from shutil import copyfile
import shutil
import sys
from dataManipulation import *

class DataSeries(object):
    def __init__(self, xData, yData, stdDevData, name):
        self.xData      = xData
        self.yData      = yData
        self.stdDevData = stdDevData
        self.name       = name


colors = iter(matplotlib.cm.rainbow(np.linspace(0, 1, 3)))

def plotDataSeries(figureNumber, dataSeriesList, title, xLabel = "Epochs", yLabel = "Average Reward", saveFigure = ""):

    numSeries = len(dataSeriesList)
    fig = plt.figure(figureNumber)
    sub = plt.subplot(111)

    for dataSeries in dataSeriesList:
        # plt.errorbar(dataSeries.xData, dataSeries.yData, dataSeries.stdDevData,label=dataSeries.name, color=next(colors))
        plt.errorbar(dataSeries.xData, dataSeries.yData, dataSeries.stdDevData,label=dataSeries.name)


    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.title(title)
    box = sub.get_position()
    sub.set_position([box.x0, box.y0, box.width * 0.75, box.height])
    L = plt.legend(loc='center left', bbox_to_anchor=(1.00, 0.5), prop={'size':9})
    L.draggable(state=True)
    
    if saveFigure != "":
        fig.savefig(saveFigure, dpi=fig.dpi)






def writeAvgResultFiles(directory, extensionList, sumData = False):
    resultCollectionFunction = lambda f: getResultsFromTaskFile(f, 0, 3, -1)

    for item in os.listdir(directory):
        for extension in extensionList:

            seedsDirectory = directory + "/" + item + "/" + extension + "/"
            masterData = computeAverageOverMultipleSeeds(seedsDirectory, sumData, resultCollectionFunction)

            for i in xrange(len(masterData)):
                writeDataToFile(seedsDirectory +"task_"+str(i)+"_results_Avg.csv",masterData[i][0], masterData[i][1], masterData[i][2])




def createComparisonDataSeries(directory, romStringList, taskIDList, taskPrefixList, extensionList, baselineDirectory, divided = True):
    #romStringList, taskIDList and taskPrefixList must be of the same size
    if len(romStringList) != len(taskIDList) and len(taskIDList) != len(taskPrefixList):
        raise Exception("Lists are not of equal size cant parse data properly")

    counter = 0
    gameDict = {}
    minNumTasks = -1
    maxNumTasks = float('inf')
    gameTitle = romStringList[0].split(',')[taskIDList[0]]

    for g in xrange(len(taskPrefixList)):
        gameDict[g] = {}

        
    for romString in romStringList:
        pathToArchs = (directory + "/" + romString)
        games = romString.split(",")
        numTasksinRomString = len(games)

        if numTasksinRomString > minNumTasks:
            minNumTasks = numTasksinRomString
        if numTasksinRomString > maxNumTasks:
            maxNumTasks = numTasksinRomString

        for arch in extensionList:
            archDirectory = pathToArchs + "/" + arch
            taskID = taskIDList[counter]
            taskFile = "/task_" + str(taskID) + "_results_Avg.csv"
            gameDict[counter][arch] = getResultsFromTaskFile(archDirectory + "/" + taskFile)

            if divided:
                    gameDict[counter][arch][0] = divideDataElementsByFactor(gameDict[counter][arch][0], numTasksinRomString)

        counter += 1


    baselineFile = baselineDirectory + "/" + gameTitle + "/DQNNet/task_0_results_Avg.csv"
    gameDict["baseline"] = getResultsFromTaskFile(baselineFile)

    if divided:       
        numDataPointsToUse = int(len(gameDict["baseline"][0]) / (minNumTasks / 2))
        gameDict["baseline"][0] = gameDict["baseline"][0][0:numDataPointsToUse]
        gameDict["baseline"][1] = gameDict["baseline"][1][0:numDataPointsToUse]
        gameDict["baseline"][2] = gameDict["baseline"][2][0:numDataPointsToUse]



    taskDataSeriesList = []
    baselineDataSeries = DataSeries(gameDict["baseline"][0], gameDict["baseline"][1], gameDict["baseline"][2], gameTitle + "_Baseline")

    counter = 0
    plotcount = 1
    for romString in romStringList:
        for arch in extensionList:
            currentArchDataSeries = DataSeries(gameDict[counter][arch][0], gameDict[counter][arch][1], gameDict[counter][arch][2], taskPrefixList[counter] + "_" + arch)
            taskDataSeriesList.append(currentArchDataSeries)
        counter += 1

    taskDataSeriesList.append(baselineDataSeries)

    plotDataSeries(plotcount, taskDataSeriesList, gameTitle + "_" + ",".join(extensionList)+"_GameComparison", saveFigure = directory + "/" + gameTitle + "_" + ",".join(extensionList)+"_GameComparison")
    plt.show()





def createExperimentDataSeries(directory, baselineDirectory, romString, summed = True, divided = True):
    pathToArchs = (directory + "/" + romString)
    games = romString.split(",")
    numTasks = len(games)
    gameDict = {}
    archList = []

    for g in games:
        gameDict[g] = {}

    #load transfer part
    for arch in os.listdir(pathToArchs):
        if "." in arch:
            continue #Not a directory

        archList.append(arch)
        archDirectory = pathToArchs + "/" + arch

        for file in os.listdir(archDirectory):
            if "results" in file and ".csv" in file:

                taskNum = int(file[file.index('_') + 1 : file.index('_results')])
                currentGame = games[taskNum]
                gameDict[currentGame][arch] = getResultsFromTaskFile(archDirectory + "/" + file)
                
                if divided:
                    gameDict[currentGame][arch][0] = divideDataElementsByFactor(gameDict[currentGame][arch][0], numTasks)
                
                if summed:
                    gameDict[currentGame][arch][1] = computeSummedData(gameDict[currentGame][arch][1])
                    gameDict[currentGame][arch][2] = gameDict[currentGame][arch][2] ** 2
                    gameDict[currentGame][arch][2] = computeSummedData(gameDict[currentGame][arch][2]) ** 0.5

    #load baselines
    count = 1
    for game in games:
        baselineFile = baselineDirectory + "/" + game + "/DQNNet/task_0_results_Avg.csv"
        gameDict[game]["baseline"] = getResultsFromTaskFile(baselineFile)

        if divided:       
            numDataPointsToUse = int(len(gameDict[game]["baseline"][0]) / (numTasks / 2))
            gameDict[game]["baseline"][0] = gameDict[game]["baseline"][0][0:numDataPointsToUse]
            gameDict[game]["baseline"][1] = gameDict[game]["baseline"][1][0:numDataPointsToUse]
            gameDict[game]["baseline"][2] = gameDict[game]["baseline"][2][0:numDataPointsToUse]

        if summed:
                    gameDict[game]["baseline"][1] = computeSummedData(gameDict[game]["baseline"][1])
                    gameDict[game]["baseline"][2] = gameDict[game]["baseline"][2] ** 2
                    gameDict[game]["baseline"][2] = computeSummedData(gameDict[game]["baseline"][2]) ** 0.5


        taskDataSeriesList = []
        baselineDataSeries = DataSeries(gameDict[game]["baseline"][0], gameDict[game]["baseline"][1], gameDict[game]["baseline"][2], game)

        for arch in archList:
            currentArchDataSeries = DataSeries(gameDict[game][arch][0], gameDict[game][arch][1], gameDict[game][arch][2], game + "_" + arch)
            taskDataSeriesList.append(currentArchDataSeries)
        
        taskDataSeriesList.append(baselineDataSeries)

        if summed:
            titleSuffix = "summed"
        else:
            titleSuffix = ""

        plotDataSeries(count, taskDataSeriesList, romString, saveFigure = pathToArchs + "/" + game + "_"+titleSuffix+"Graph")
        count += 1
    plt.show()


def test2(file, t):
    res = getResultsFromTaskFile(file)
    d = DataSeries(res[0], res[1], res[2], t)
    plotDataSeries(1, [d], t, saveFigure = file + "/" + t + "_Avg")
    plt.show()

def test3(directory):
    count = 1
    for item in os.listdir(directory):
        taskDirectory = directory + "/" + item + "/DQNNet/"
        taskFile = taskDirectory + "task_0_results_Avg.csv"
        res = getResultsFromTaskFile(taskFile)
        d = DataSeries(res[0], res[1], res[2], item)
        plotDataSeries(count, [d], item, saveFigure = taskDirectory + "/" + item + "_Avg")

        count += 1
    plt.show()


def test4(directory1, directory2, summed = True):
    count = 1
    for item in os.listdir(directory1):

        taskDirectory1 = directory1 + "/" + item + "/DQNNet/"
        taskDirectory2 = directory2 + "/" + item + "/DQNNet/"

        taskFile1 = taskDirectory1 + "task_0_results_Avg.csv"
        taskFile2 = taskDirectory2 + "task_0_results_Avg.csv"

        res1 = getResultsFromTaskFile(taskFile1)
        res2 = getResultsFromTaskFile(taskFile2)

        if summed:
            res1[1] = computeSummedData(res1[1])
            res1[2] = res1[2] ** 2
            res1[2] = computeSummedData(res1[2]) ** 0.5

            res2[1] = computeSummedData(res2[1])
            res2[2] = res2[2] ** 2
            res2[2] = computeSummedData(res2[2]) ** 0.5

        d1 = DataSeries(res1[0], res1[1], res1[2], item + "_Minimal")
        d2 = DataSeries(res2[0], res2[1], res2[2], item + "_Full")

        if summed:
            titleSuffix = "summed"
        else:
            titleSuffix = ""

        plotDataSeries(count, [d1, d2], item + " Full vs Minimal " + titleSuffix, saveFigure = "transferBaselinesCompare" + "/" + item + "_"+titleSuffix+"Avg")

        count += 1

    plt.show()


#folderToDelete = "/M0^0^0^0_D0^0^0^0"
def moveFoldersUp(baseFolder, folderToDelete):
    for f in os.listdir(baseFolder):
        for f2 in os.listdir(baseFolder + "/" + f + folderToDelete):
            shutil.move(baseFolder + "/" + f + "/" + folderToDelete +"/"+ f2, baseFolder + "/" +f)
        shutil.rmtree(baseFolder + "/" + f + "/" + folderToDelete)

def main(args):
    # test("transferBaselinesCompiled/")
    # test2("transferBaselinesCompiled/pong/DQNNet/task_0_results_Avg.csv", "Pong")
    # test("transferBaselinesFullCompiled/")
    # test3("transferBaselinesCompiled/")
    # test4("transferBaselinesCompiled/", "transferBaselinesFullCompiled/")




    # writeAvgResultFiles("../compiledResults/dqnFullBaselineResult/", ["DQNNet"], True)
    # writeAvgResultFiles("../compiledResults/dqnMinBaselineResult/", ["DQNNet"], True)
    # writeAvgResultFiles("../compiledResults/transferMultigameResult/", ["DQNNet", "FirstRepresentationSwitchNet", "PolicySwitchNet"], True)
    # return

    # romStringList = ["assault,demon_attack,space_invaders,phoenix", "enduro,demon_attack,pong,space_invaders", "enduro,pong,gopher,space_invaders"]
    # romStringList = ["assault,demon_attack,space_invaders,phoenix", "enduro,demon_attack,pong,space_invaders"]
    romStringList = ["enduro,demon_attack,pong,space_invaders", "enduro,pong,gopher,space_invaders"]
    taskIDList = [0, 0]
    # taskPrefixList = ["4Similar", "2Similar", "NonSimilar"]

    taskPrefixList = ["2Similar", "NonSimilar"]
    # taskPrefixList = ["4Similar", "2Similar", "NonSimilar"]

    extensionList = ["DQNNet", "FirstRepresentationSwitchNet", "PolicySwitchNet"]
    # extensionList = ["DQNNet"]
    # extensionList = ["PolicySwitchNet"]
    # extensionList = ["FirstRepresentationSwitchNet"]


    baselineDirectory = "../compiledResults/dqnMinBaselineResult/"
    createComparisonDataSeries("../compiledResults/transferMultigameResult", romStringList, taskIDList, taskPrefixList, extensionList, baselineDirectory, divided = True)
    return

    if len(args) > 0:
        t = int(args[0])
    else:
        t = 0

    if t == 0:
        createExperimentDataSeries("../compiledResults/transferMultigameResult/", "../compiledResults/dqnMinBaselineResult/", "assault,demon_attack,space_invaders,phoenix", False)
    elif t == 1:
        createExperimentDataSeries("../compiledResults/transferMultigameResult/", "../compiledResults/dqnMinBaselineResult/", "enduro,demon_attack,pong,space_invaders", False)
    elif t == 2:
        createExperimentDataSeries("../compiledResults/transferMultigameResult/", "../compiledResults/dqnMinBaselineResult/", "enduro,pong,gopher,space_invaders", False)



if __name__ == "__main__":
    main(sys.argv[1:])




