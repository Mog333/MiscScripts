import matplotlib.pyplot as plt
import re
import os
import shutil
import sys
import dataManipulation  
import math
from pylab import *
from shutil import copyfile
from scipy import stats


#Global for every program run to always increment and use a new plot
plotCount           = 1



class DataSeries(object):
    def __init__(self, xData, yData, stdDevData, name):
        self.xData      = xData
        self.yData      = yData
        self.stdDevData = stdDevData
        self.name       = name


class PlotWrapper(object):
    def __init__(self, title, xLabel, yLabel, dataSeriesList = []):
        self.dataSeriesList = dataSeriesList
        self.title = title
        self.xLabel = xLabel
        self.yLabel = yLabel


    def addDataSeries(self, dataSeries):
        self.dataSeriesList.append(dataSeries)


    def createPlot(self, figureNumber = 1, filenameToSave = ""):
        figure = plt.figure(figureNumber)
        subplot = plt.subplot(111)
        colors = iter(matplotlib.cm.rainbow(np.linspace(0, 1, len(self.dataSeriesList))))


        for dataSeries in self.dataSeriesList:
            if dataSeries.stdDevData != None:
                #For this current run, should be calculated elsewhere
                numSamples  = 30
                alpha       = 0.05
                tValue      = stats.t.ppf(1-alpha, numSamples - 1)

                plt.errorbar(dataSeries.xData, dataSeries.yData, dataSeries.stdDevData * tValue / math.sqrt(numSamples) ,label=dataSeries.name, color=next(colors))
                #plt.errorbar(dataSeries.xData, dataSeries.yData, dataSeries.stdDevData*1.96,label=dataSeries.name, color=next(colors))
                # plt.errorbar(dataSeries.xData, dataSeries.yData, [dataSeries.stdDevData * 0.69, dataSeries.stdDevData * 1.83],label=dataSeries.name, color=next(colors))
            else:
                plt.errorbar(dataSeries.xData, dataSeries.yData, None,label=dataSeries.name, color=next(colors))

            # plt.errorbar(dataSeries.xData, dataSeries.yData, dataSeries.stdDevData,label=dataSeries.name)

        plt.xlabel(self.xLabel)
        plt.ylabel(self.yLabel)
        plt.title(self.title)
        box = subplot.get_position()
        subplot.set_position([box.x0, box.y0, box.width * 0.75, box.height])
        L = plt.legend(loc='center left', bbox_to_anchor=(1.00, 0.5), prop={'size':9})
        L.draggable(state=True)
        
        if filenameToSave != "":
            figure.savefig(filenameToSave, dpi=figure.dpi)


def plotDataSeries(figureNumber, dataSeriesList, title, xLabel = "Epochs", yLabel = "Average Reward", saveFigure = ""):
    fig = plt.figure(figureNumber)
    sub = plt.subplot(111)

    colors = iter(matplotlib.cm.rainbow(np.linspace(0, 1, len(dataSeriesList))))


    for dataSeries in dataSeriesList:
        numSamples  = 30
        alpha       = 0.05
        tValue      = stats.t.ppf(1-alpha, numSamples - 1)

        plt.errorbar(dataSeries.xData, dataSeries.yData, dataSeries.stdDevData * tValue / math.sqrt(numSamples) ,label=dataSeries.name, color=next(colors))
        # plt.errorbar(dataSeries.xData, dataSeries.yData, [dataSeries.stdDevData * 0.69, dataSeries.stdDevData * 1.83],label=dataSeries.name, color=next(colors))
        
        # plt.errorbar(dataSeries.xData, dataSeries.yData, dataSeries.stdDevData,label=dataSeries.name, color=next(colors))
        # plt.errorbar(dataSeries.xData, dataSeries.yData, dataSeries.stdDevData,label=dataSeries.name)


    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.title(title, y=1.01)
    box = sub.get_position()
    sub.set_position([box.x0, box.y0, box.width * 0.75, box.height])
    L = plt.legend(loc='center left', bbox_to_anchor=(1.00, 0.5), prop={'size':9})
    L.draggable(state=True)
    
    if saveFigure != "":
        fig.savefig(saveFigure, dpi=fig.dpi)





def createComparisonDataSeries(directory, romStringList, taskIDList, taskPrefixList, extensionList, baselineDirectory, summed = False, divided = True, resultsCollectionFunction = dataManipulation.getResultsFromTaskFile, taskSeparator = "^"):
    #romStringList, taskIDList and taskPrefixList must be of the same size
    if len(romStringList) != len(taskIDList) and len(taskIDList) != len(taskPrefixList):
        raise Exception("Lists are not of equal size cant parse data properly")

    global plotCount
    counter = 0
    gameDict = {}
    minNumTasks = -1
    maxNumTasks = float('inf')
    gameTitle = romStringList[0].split(taskSeparator)[taskIDList[0]]


    for g in xrange(len(taskPrefixList)):
        gameDict[g] = {}

        
    for romString in romStringList:
        pathToArchs = (directory + "/" + romString)
        games = romString.split(taskSeparator)
        numTasksinRomString = len(games)

        if numTasksinRomString > minNumTasks:
            minNumTasks = numTasksinRomString
        if numTasksinRomString > maxNumTasks:
            maxNumTasks = numTasksinRomString

        for arch in extensionList:
            archDirectory = pathToArchs + "/" + arch
            taskID = taskIDList[counter]
            if summed:
                taskFile = "/averaged_task_" + str(taskID) + "_results_Summed.csv"
            else:
                taskFile = "/averaged_task_" + str(taskID) + "_results.csv"

            gameDict[counter][arch] = resultsCollectionFunction(archDirectory + "/" + taskFile)

            if divided:
                    gameDict[counter][arch][0] = dataManipulation.divideDataElementsByFactor(gameDict[counter][arch][0], numTasksinRomString)

                    if summed:
                        gameDict[counter][arch][1] = dataManipulation.divideDataElementsByFactor(gameDict[counter][arch][1], numTasksinRomString)

        counter += 1


    taskDataSeriesList  = []
    counter             = 0
    for romString in romStringList:
        for arch in extensionList:
            currentArchDataSeries = DataSeries(gameDict[counter][arch][0], gameDict[counter][arch][1], gameDict[counter][arch][2], taskPrefixList[counter] + "_" + arch)
            taskDataSeriesList.append(currentArchDataSeries)
        counter += 1



    ### If a baseline is provided in a different directory (ie run multigame experiment, then compare one of the tasks to a separate experiment of running just that task)
    if baselineDirectory != None:
        if summed:
            baselineFile = baselineDirectory + "/" + gameTitle + "/DQNNet/averaged_task_0_results_Summed.csv"
        else:
            baselineFile = baselineDirectory + "/" + gameTitle + "/DQNNet/averaged_task_0_results.csv"

        gameDict["baseline"] = resultsCollectionFunction(baselineFile)

        if divided:
            #When dividing the experiment data you only want to compare to the baselines first 
            numDataPointsToUse = int(len(gameDict["baseline"][0]) / (minNumTasks / 2))
            gameDict["baseline"][0] = gameDict["baseline"][0][0:numDataPointsToUse]
            gameDict["baseline"][1] = gameDict["baseline"][1][0:numDataPointsToUse]
            gameDict["baseline"][2] = gameDict["baseline"][2][0:numDataPointsToUse]



        baselineDataSeries = DataSeries(gameDict["baseline"][0], gameDict["baseline"][1], gameDict["baseline"][2], gameTitle + "_Baseline")
        taskDataSeriesList.append(baselineDataSeries)

    


    yLabel = "Average Reward"
    titleSuffix = ""
    if summed:
        yLabel = "Average Summed Reward"
        titleSuffix = "Summed"

    if len(extensionList) == 1:
        extensionSuffix = extensionList[0]
    elif len(extensionList) == 2 and "disjointDQNNet" in extensionList:
        extensionSuffix = extensionList[0] + "_with_Baseline"
    else:
        extensionSuffix = "All_Architectures"

    filename = gameTitle + "_" + titleSuffix + "_" + extensionSuffix + "_" + "Multi-experiment Comparison"
    title = gameTitle + " " + titleSuffix + "\n" + extensionSuffix + " " + "Multi-experiment Comparison"

    plotDataSeries(plotCount, taskDataSeriesList, title, yLabel = yLabel, saveFigure = directory + "/" + filename)
    # plotDataSeries(plotCount, taskDataSeriesList, gameTitle + "_" + ",".join(extensionList)+"_GameComparison", yLabel = yLabel, saveFigure = directory + "/" + gameTitle + titleSuffix + "_" + ",".join(extensionList)+"_GameComparison")
    plotCount += 1





def createExperimentDataSeries(directory, baselineDirectory, romString, summed = True, divided = True, resultsCollectionFunction = dataManipulation.getResultsFromTaskFile,taskSeparator = "^"):
    pathToArchs = (directory + "/" + romString)
    games = romString.split(taskSeparator)
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
            if "results" in file and ".csv" in file and ((not summed and "Summed" not in file) or (summed and "Summed" in file)):
                print archDirectory + "/" + file
                taskNum = int(file[file.index('task_') + 5 : file.index('_results')])
                currentGame = games[taskNum]
                gameDict[currentGame][arch] = resultsCollectionFunction(archDirectory + "/" + file)
                
                if divided:
                    gameDict[currentGame][arch][0] = dataManipulation.divideDataElementsByFactor(gameDict[currentGame][arch][0], numTasks)

                    if summed:
                        gameDict[currentGame][arch][1] = dataManipulation.divideDataElementsByFactor(gameDict[currentGame][arch][1], numTasks)


    graphSuffix = ""
    yLabel = "Average Reward"
    if summed:
        graphSuffix = "_Summed"
        yLabel = "Average Summed Reward"

    count = 1
    for game in games:
        taskDataSeriesList = []

        if baselineDirectory != None:
            #load baselines

            if summed:
                extensionToFile = "/DQNNet/averaged_task_0_results_Summed.csv"
            else:
                extensionToFile = "/DQNNet/averaged_task_0_results.csv"

            baselineFile = baselineDirectory + "/" + game + extensionToFile
            gameDict[game]["baseline"] = resultsCollectionFunction(baselineFile)

            if divided:       
                numDataPointsToUse = int(len(gameDict[game]["baseline"][0]) / (numTasks / 2))
                gameDict[game]["baseline"][0] = gameDict[game]["baseline"][0][0:numDataPointsToUse]
                gameDict[game]["baseline"][1] = gameDict[game]["baseline"][1][0:numDataPointsToUse]

                if gameDict[game]["baseline"][2] != None:
                    gameDict[game]["baseline"][2] = gameDict[game]["baseline"][2][0:numDataPointsToUse]

            baselineDataSeries = DataSeries(gameDict[game]["baseline"][0], gameDict[game]["baseline"][1], gameDict[game]["baseline"][2], game)
            taskDataSeriesList.append(baselineDataSeries)

        


        for arch in archList:
            currentArchDataSeries = DataSeries(gameDict[game][arch][0], gameDict[game][arch][1], gameDict[game][arch][2], game + "_" + arch )
            taskDataSeriesList.append(currentArchDataSeries)
        

        plotDataSeries(count, taskDataSeriesList, game + graphSuffix, yLabel = yLabel, saveFigure = pathToArchs + "/" + game + graphSuffix)
        # plotDataSeries(count, taskDataSeriesList, romString + graphSuffix, yLabel = yLabel, saveFigure = pathToArchs + "/" + game + graphSuffix +"_Graph")
        count += 1
    # plt.show()



def plotSingleResultFile(pathToFile, title, xLabel = 'Epoch Number', yLabel = 'AverageReward', plotNumber = 1, saveToName = '', resultsCollectionFunction = dataManipulation.getResultsFromTaskFile, showPlot = True):
    results = resultsCollectionFunction(pathToFile)
    strippedFileName = dataManipulation.getFilenameWithoutExtension(dataManipulation.getFilenameFromPath(pathToFile))
    resultsDataSeries = DataSeries(results[0], results[1], results[2], title)
    p = PlotWrapper(title, xLabel, yLabel, [resultsDataSeries])
    p.createPlot(plotNumber, saveToName)
    if showPlot:
        plt.show()



def plotAllAveragedSingleGraphsForDirectory(experimentDirectory, architectureList = ["DQNNet", "FirstRepresentationSwitchNet", "PolicySwitchNet"], taskSeparator = "^"):
    resultsCollectionFunction        = lambda f: dataManipulation.getResultsFromTaskFile(f, 0, 1, 2)

    if experimentDirectory[-1] == "/":
        taskString = experimentDirectory[experimentDirectory[0:-1].rindex("/") + 1:-1]
    else:
        taskString = experimentDirectory[experimentDirectory.rindex("/") + 1:]


    taskList   = taskString.split(taskSeparator)
    numTasks   = len(taskList)
    print taskString
    print taskList
    global plotCount

    # plotCount = 1
    for architecture in architectureList:
        archDirectory = experimentDirectory + "/" + architecture
        contents = os.listdir(archDirectory)
        resultFiles = [c for c in contents if (".csv" in c and "results" in c)]
        for resultFile in resultFiles:
            taskNum = resultFile[resultFile.index("task_") + 5:resultFile.index("_results")]

            title = taskList[int(taskNum)]
            suffix = resultFile[resultFile.index("_results") + 8: resultFile.index(".")]

            yLabel = "Average Reward"
            if "Summed" in suffix:
                yLabel = "Average Summed Reward"

            resultFilePath = archDirectory + "/" + resultFile
            saveToFilePath = archDirectory + "/" + "graph_" + title + suffix
            plotSingleResultFile(resultFilePath, title + suffix, xLabel = 'Epoch Number', yLabel = yLabel, plotNumber =  plotCount, saveToName = saveToFilePath, resultsCollectionFunction = resultsCollectionFunction, showPlot = False)
            plotCount += 1

    # plt.show()


#Removable not in use
def createExperimentDataSeriesOld(directory, baselineDirectory, romString, summed = True, divided = True):
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
                gameDict[currentGame][arch] = dataManipulation.getResultsFromTaskFile(archDirectory + "/" + file)
                
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
        gameDict[game]["baseline"] = dataManipulation.getResultsFromTaskFile(baselineFile)

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
    # plt.show()
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


def main(args):

    resultsCollectionFunction        = lambda f: dataManipulation.getResultsFromTaskFile(f, 0, 3, -1)
    resultsCollectionFunctionSummed  = lambda f: dataManipulation.getResultsFromTaskFile(f, 0, 1, 2)

    baselineDirectory = None
    experimentBase    =  "/home/robert/Desktop/Research/MultiGameResults/20EpochResultsOnly/"
    romStringList     = ["assault^demon_attack^space_invaders^phoenix", "enduro^demon_attack^pong^space_invaders", "enduro^pong^gopher^space_invaders"]
    
    extensionList     = ["DQNNet", "FirstRepresentationSwitchNet", "PolicySwitchNet", "disjointDQNNet"]
    # extensionList = ["DQNNet"]
    # extensionList = ["Disjoint"]
    # extensionList = ["PolicySwitchNet"]
    # extensionList = ["FirstRepresentationSwitchNet"]

    # createExperimentDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", "/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/DqnBaselines", "assault^demon_attack^space_invaders^phoenix", summed = False, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)
    # createExperimentDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", "/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/DqnBaselines", "enduro^demon_attack^pong^space_invaders", summed = False, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)
    # createExperimentDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", "/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/DqnBaselines", "enduro^pong^gopher^space_invaders", summed = False, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)

    # createExperimentDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", "/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/DqnBaselines", "assault^demon_attack^space_invaders^phoenix", summed = True, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)
    # createExperimentDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", "/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/DqnBaselines", "enduro^demon_attack^pong^space_invaders", summed = True, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)
    createExperimentDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", "/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/DqnBaselines", "enduro^pong^gopher^space_invaders", summed = True, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)
    return

    ###
    # Creates a graphs in the experiment  + architectures directory for every result file
    ###

    # plotAllAveragedSingleGraphsForDirectory(experimentBase + "/" + romStringList[0], extensionList)
    # plotAllAveragedSingleGraphsForDirectory(experimentBase + "/" + romStringList[1], extensionList)
    # plotAllAveragedSingleGraphsForDirectory(experimentBase + "/" + romStringList[2], extensionList)
    # return



    ###
    # Creates comparisons between different architectures for the same task in a multigame experiment
    ###

    # createExperimentDataSeries(experimentBase, baselineDirectory, romStringList[0], summed = True, divided = False, resultsCollectionFunction = resultsCollectionFunctionSummed)
    # createExperimentDataSeries(experimentBase, baselineDirectory, romStringList[1], summed = True, divided = False, resultsCollectionFunction = resultsCollectionFunctionSummed)
    # createExperimentDataSeries(experimentBase, baselineDirectory, romStringList[2], summed = True, divided = False, resultsCollectionFunction = resultsCollectionFunctionSummed)
    # createExperimentDataSeries(experimentBase, baselineDirectory, romStringList[0], summed = False, divided = False, resultsCollectionFunction = resultsCollectionFunctionSummed)
    # createExperimentDataSeries(experimentBase, baselineDirectory, romStringList[1], summed = False, divided = False, resultsCollectionFunction = resultsCollectionFunctionSummed)
    # createExperimentDataSeries(experimentBase, baselineDirectory, romStringList[2], summed = False, divided = False, resultsCollectionFunction = resultsCollectionFunctionSummed)
    # return


    

    ###
    # Creates the across experiment same game comparison graphs
    # ie compare space invaders with 3 other shooting games vs with 1/0 other similar shooting games
    # Do this for both one architecture, and all architectures (which is too messy to analyse?)
    # Creates graphs for both summed and nonsummed data
    # Only one of the set of three variables should be uncommented to run the program
    ###

    #Compare space invaders
    romStringList   = ["assault^demon_attack^space_invaders^phoenix", "enduro^demon_attack^pong^space_invaders", "enduro^pong^gopher^space_invaders"]
    taskPrefixList  = ["4Similar", "2Similar", "NonSimilar"]
    taskIDList      = [2, 3, 3]
    # romStringList = ["assault^demon_attack^space_invaders^phoenix", "enduro^demon_attack^pong^space_invaders", "enduro^pong^gopher^space_invaders"]
    # taskPrefixList = ["4Similar", "2Similar", "NonSimilar"]
    # taskIDList = [2, 3, 3]
    
    #compare demon attack
    # romStringList = ["assault^demon_attack^space_invaders^phoenix", "enduro^demon_attack^pong^space_invaders"]
    # taskPrefixList = ["4Similar", "2Similar"]
    # taskIDList = [1, 1]
    
    # compare enduro
    # romStringList = ["enduro^demon_attack^pong^space_invaders", "enduro^pong^gopher^space_invaders"]
    # taskPrefixList = ["2Similar", "NonSimilar"]
    # taskIDList = [0, 0]
    romStringList = ["enduro^demon_attack^pong^space_invaders", "enduro^pong^gopher^space_invaders"]
    taskPrefixList = ["2Similar", "NonSimilar"]
    taskIDList = [0, 0]

    

    # baselineDirectory = "/home/robert/Desktop/Research/CompiledResults/testStructure/DqnBaselines"
    divided = False


    ###
    #   Compare one architecture with and without the baseline ascross experiments
    ###
    
    # for e in extensionList:
        ###
        #   Compare One architecture across experiments
        ###
        # createComparisonDataSeries(experimentBase, romStringList, taskIDList, taskPrefixList, [e], baselineDirectory, summed = False, divided = divided, resultsCollectionFunction = resultsCollectionFunctionSummed)
        # createComparisonDataSeries(experimentBase, romStringList, taskIDList, taskPrefixList, [e], baselineDirectory, summed = True,  divided = divided, resultsCollectionFunction = resultsCollectionFunctionSummed)


        ###
        #   Compare One architecture and disjointDQN (Baseline) across experiments 
        ###


        # if e == "disjointDQNNet":
        #     continue

        # eList = []
        # eList.append(e)
        # eList.append("disjointDQNNet")

    baselineDirectory = "/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/DqnBaselines"

    for e in extensionList:
        createComparisonDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", romStringList, taskIDList, taskPrefixList, [e], baselineDirectory, summed = False, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)
        createComparisonDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", romStringList, taskIDList, taskPrefixList, [e], baselineDirectory, summed = True, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)

        # createComparisonDataSeries(experimentBase, romStringList, taskIDList, taskPrefixList, eList, baselineDirectory, summed = True,  divided = divided, resultsCollectionFunction = resultsCollectionFunctionSummed)


    ###
    # Compare All architectures across experiments
    ###

    # createComparisonDataSeries(experimentBase, romStringList, taskIDList, taskPrefixList, extensionList, baselineDirectory, summed = False, divided = divided, resultsCollectionFunction = resultsCollectionFunctionSummed)
    createComparisonDataSeries(experimentBase, romStringList, taskIDList, taskPrefixList, extensionList, baselineDirectory, summed = True,  divided = divided, resultsCollectionFunction = resultsCollectionFunctionSummed)


    plt.show()

    createComparisonDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", romStringList, taskIDList, taskPrefixList, extensionList, baselineDirectory, summed = False, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)
    createComparisonDataSeries("/home/robpost/Desktop/ResearchDevelopment/MiscScripts/CompiledResults/testStructure/transferMultigameResult", romStringList, taskIDList, taskPrefixList, extensionList, baselineDirectory, summed = True, divided = True, resultsCollectionFunction = resultsCollectionFunctionSummed)

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




