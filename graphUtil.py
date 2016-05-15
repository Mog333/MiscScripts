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



def plotDataSeries(figureNumber, dataSeriesList, title, xLabel = "Epochs", yLabel = "Average Reward", saveFigure = ""):

    numSeries = len(dataSeriesList)
    fig = plt.figure(figureNumber)
    sub = plt.subplot(111)

    for dataSeries in dataSeriesList:
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


def test5(directory):
    pass




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

    # writeAvgResultFiles("transferBaselinesCompiled/", ["DQNNet"], True)
    # writeAvgResultFiles("transferGamesCompiled/", ["DQNNet", "FirstRepresentationSwitchNet", "PolicySwitchNet"], True)
    # return
    if len(args) > 0:
        t = int(args[0])
    else:
        t = 0

    if t == 0:
        createExperimentDataSeries("transferGamesCompiled/", "transferBaselinesCompiled", "assault,demon_attack,space_invaders,phoenix", False)
    elif t == 1:
        createExperimentDataSeries("transferGamesCompiled/", "transferBaselinesCompiled", "enduro,demon_attack,pong,space_invaders", False)
    elif t == 2:
        createExperimentDataSeries("transferGamesCompiled/", "transferBaselinesCompiled", "enduro,pong,gopher,space_invaders", False)



if __name__ == "__main__":
    main(sys.argv[1:])




