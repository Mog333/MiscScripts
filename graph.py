from pylab import *
import matplotlib.pyplot as plt
import re
import os
from shutil import copyfile
import shutil
import sys


archs = ["DQNNet", 
    "PolicySwitchNet", 
    "PolicyPartialSwitchNet", 
    "TaskTransformationNet",  
    "FirstRepresentationSwitchNet"
        ]

hasCharacters = re.compile("[a-zA-Z]")


def getResultsFromTaskFile(filename):
    resFile = open(filename, 'r')
    rewards = []
    epochs  = []

    line = resFile.readline()
    while  line != "":
        if line == '\n' or line == '':
            continue

        if hasCharacters.match(line) != None:
            line = resFile.readline()
            continue
 
        contents = line.split(",")
        epochs.append(int(contents[0].strip()))
        rewards.append(float(contents[3].strip()))
        line = resFile.readline()

    resFile.close()
 
    return (epochs, rewards)







def collectDataFromMultigameExperiment(directory, gameString):
    baselineDataFiles = directory + "/" + gameString + "/baselines/"
    games = gameString.split(",")
    gameData = {}
    numTasks = len(games)

    for index in range(numTasks):
        gameData["task_" + str(index)] = {}


    for folder in os.listdir(baselineDataFiles):
        if not os.path.isdir(baselineDataFiles + "/" + folder):
            continue
        if folder not in games:
            continue

        taskIndex = games.index(folder)
        baselineDataFile = baselineDataFiles + "/" + folder + "/task_0_results.csv"
        baselineData = getResultsFromTaskFile(baselineDataFile)
        gameData["task_" + str(taskIndex)]["baselineData"] = baselineData

    for arch in archs:
        archDirectory = directory + "/" + gameString + "/" + arch + "/"
        if not os.path.isdir(archDirectory):
            continue

        for taskID in xrange(0,numTasks):
            archDataFile = archDirectory + "task_" + str(taskID) + "_results.csv"
            taskArchData = getResultsFromTaskFile(archDataFile)
            gameData["task_" + str(taskID)][arch + "Data"] = taskArchData
    return gameData

def collectDataFromMultiFlavorExperiment(directory, gameFlavorString):
    modeOrDiffString = gameFlavorString.split("_")[1].split(",")
    folderPrefix = modeOrDiffString[0][0]
    modeOrDiffString[0] = modeOrDiffString[0][1:]
    numTasks = len(modeOrDiffString)
    print modeOrDiffString
    baselineDataFiles = directory + "/" + gameFlavorString + "/baselines/"
    gameData = {}

    for index in modeOrDiffString:
        gameData["task_" + str(index)] = {}
        taskBaselineFolder = baselineDataFiles + "/" + folderPrefix + str(index)
        if not os.path.isdir(taskBaselineFolder):
            continue

        taskBaselineDataFile = taskBaselineFolder + "/task_0_results.csv"
        baselineData = getResultsFromTaskFile(taskBaselineDataFile)
        gameData["task_" + str(index)]["baselineData"] = baselineData

    for arch in archs:
        archDirectory = directory + "/" + gameFlavorString + "/" + arch + "/"
        if not os.path.isdir(archDirectory):
            continue

        for taskID in xrange(0,numTasks):
            archDataFile = archDirectory + "task_" + str(taskID) + "_results.csv"
            taskArchData = getResultsFromTaskFile(archDataFile)
            gameData["task_" + str(taskID)][arch + "Data"] = taskArchData
    return gameData


def test():
    # plotMultigameResults("resultsCompile1", "pong,breakout")
    plotMultiModeResults("resultsCompile1", "hero_M0,1,2,3,4")

def plotMultiModeResults(directory, gameModeString):
    gameModeStringComponents = gameModeString.split("_")
    gameName = gameModeStringComponents[0]
    modeOrDiffString = gameModeStringComponents[1].split(",")
    folderPrefix = modeOrDiffString[0][0]
    modeOrDiffString[0] = modeOrDiffString[0][1:]
    numTasks = len(modeOrDiffString)
    data = collectDataFromMultiFlavorExperiment(directory, gameModeString)

    for i in xrange(numTasks):
        fig = plt.figure(i + 1)
        sub = plt.subplot(111)
        taskData = data["task_" + str(modeOrDiffString[i])]

        for arch in archs:
            plt.plot(taskData[arch + "Data"][0], taskData[arch + "Data"][1], label=arch)

        plt.plot(taskData["baselineData"][0], taskData["baselineData"][1], label="Baseline")
 
        plt.xlabel('Epochs')
        plt.ylabel('Average Reward')
        plt.title(gameName + " " + folderPrefix + str(modeOrDiffString[i]))
        # plt.ylim([-0.5, 100])
        # plt.xlim([0, 200])
 
        box = sub.get_position()
        sub.set_position([box.x0, box.y0, box.width * 0.75, box.height])
        L = plt.legend(loc='center left', bbox_to_anchor=(1.00, 0.5), prop={'size':9})
        L.draggable(state=True)
        fig.savefig(gameModeString + "_" + modeOrDiffString[i], dpi=fig.dpi)

    plt.show()

def plotMultigameResults(directory, gameString):
    games = gameString.split(",")
    numTasks = len(games)
    data = collectDataFromMultigameExperiment(directory, gameString)

    for i in xrange(numTasks):
        fig = plt.figure(i + 1)
        sub = plt.subplot(111)
        taskData = data["task_" + str(i)]

        for arch in archs:
            plt.plot(taskData[arch + "Data"][0], taskData[arch + "Data"][1], label=arch)

        plt.plot(taskData["baselineData"][0], taskData["baselineData"][1], label="Baseline")
 
        plt.xlabel('Epochs')
        plt.ylabel('Average Reward')
        plt.title(games[i])
        # plt.ylim([-0.5, 100])
        # plt.xlim([0, 200])
 
        box = sub.get_position()
        sub.set_position([box.x0, box.y0, box.width * 0.75, box.height])
        L = plt.legend(loc='center left', bbox_to_anchor=(1.00, 0.5), prop={'size':9})
        L.draggable(state=True)
        fig.savefig(gameString + "_" + games[i], dpi=fig.dpi)

    plt.show()





# def getResultsFromFile(filename, numTasks = 1):
#     resFile = open(filename, 'r')
#     rewards = []
#     for i in xrange(numTasks):
#         rewards.append([])
 
#     epochs  = []
#     line = resFile.readline()
#     while  line != "":
#         if line == '\n' or line == '':
#             continue
 
#         contents = line.split(",")
#         epochs.append(contents[0])
#         for i in xrange(numTasks):
#             r = float(contents[i + 1])
#             rewards[i].append(r)
 
#         line = resFile.readline()
 
#     return (epochs, rewards)
 
def plotMultiFlavorResults(directory, game, numTasks):
    flavorResults = []
    for i in xrange(1, numTasks + 1):
        resFile = directory + "/F" + str(i) + "/results.csv"
        flavorResults.append(getResultsFromFile(resFile))
 
    fullResultsFile = directory + "/fullShare" + "/results.csv"
    layerResultsFile = directory + "/layerShare" + "/results.csv"
    repResultsFile = directory + "/repShare" + "/results.csv"
 
    fullResults = getResultsFromFile(fullResultsFile, numTasks)
    layerResults = getResultsFromFile(layerResultsFile, numTasks)
    repResults = getResultsFromFile(repResultsFile, numTasks)
 
    for i in xrange(0, numTasks):
        fig = plt.figure(i + 1)
        sub = plt.subplot(111)
        plt.plot(fullResults[0][0:len(fullResults[1][i])], fullResults[1][i], label="Full Share")
        plt.plot(layerResults[0][0:len(layerResults[1][i])], layerResults[1][i], label="Layer Share")
        plt.plot(repResults[0][0:len(repResults[1][i])], repResults[1][i], label="Rep Share")
 
        plt.plot(flavorResults[i][0][0:len(flavorResults[i][1][0])], flavorResults[i][1][0], label='reduced DQN')
        plt.xlabel('epochs')
        plt.ylabel('Average Reward')
        plt.title(game + " flavor: " + str(i + 1))
        plt.ylim([-0.5, 100])
        plt.xlim([0, 200])
 
        box = sub.get_position()
        sub.set_position([box.x0, box.y0, box.width * 0.75, box.height])
 
        L = plt.legend(loc='center left', bbox_to_anchor=(1.00, 0.5))
        L.draggable(state=True)
 
        fig.savefig(game + "_flavor_" + str(i + 1), dpi=fig.dpi)
 
 
 
def plotMultiGameTaskResults(directory, game, numTasks = 2):
    filename = directory + game
    fullShareResultsFilename = filename + "_fullShare.csv"
    layerShareResultsFilename = filename + "_layerShare.csv"
    repShareResultsFilename = filename + "_repShare.csv"
 
    games = game.split(",")
    if len(games) != numTasks:
        print "The number of games is not equal to the number of tasks - not plotting"
        return
 
    fullResults = getResultsFromFile(fullShareResultsFilename, numTasks)
    layerResults = getResultsFromFile(layerShareResultsFilename, numTasks)
    repResults = getResultsFromFile(repShareResultsFilename, numTasks)
 
   
    # figure = plt.figure()
    # subplot = figure.add_subplot(111)
    # plots = []
    # for i in xrange(numTasks):
    #     plots.append(subplot.plot(fullResults[0][0:len(fullResults[1][i])], fullResults[1][i], label="FullShare: " + str(i)))
 
    # figure.suptitle(title)
   
    for i in xrange(len(games)):
        plt.figure(i + 1)
        plt.subplot(111)
        plt.plot(fullResults[0][0:len(fullResults[1][i])], fullResults[1][i], label="Full Share")
        plt.plot(layerResults[0][0:len(layerResults[1][i])], layerResults[1][i], label="Layer Share")
        plt.plot(repResults[0][0:len(repResults[1][i])], repResults[1][i], label="Rep Share")
        plt.xlabel('epochs')
        plt.ylabel('Average Reward')
        plt.title(games[i])
        L = plt.legend()
        L.draggable(state=True)
 
    # plt.figure(2)
    # plt.subplot(111)
    # plt.plot(fullResults[0][0:len(fullResults[1][1])], fullResults[1][1], label="Full Share")
    # plt.plot(layerResults[0][0:len(layerResults[1][1])], layerResults[1][1], label="Layer Share")
    # plt.plot(repResults[0][0:len(repResults[1][1])], repResults[1][1], label="Rep Share")
    # plt.xlabel('epochs')
    # plt.ylabel('Average Reward')
    # plt.title(games[1])
    # L = plt.legend()
    # L.draggable(state=True)
 
 
    # OLD
    # L = subplot.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=numTasks / 4, fancybox=True, shadow=True)
 
 
   
 
def plotTaskResults(filename, title, numTasks = 0):
    resFile = open(filename, 'r')
    line = resFile.readline()
    rewards = []
    for i in xrange(numTasks):
        rewards.append([])
 
    epochs  = []
    while  line != "":
        if line == '\n' or line == '':
            continue
 
        contents = line.split("\t")
        # print len(contents)
        # print contents
        epochs.append(contents[0])
        for i in xrange(numTasks):
            r = float(contents[i + 1])
            rewards[i].append(r)
 
        line = resFile.readline()
 
 
 
    # print rewards[i]
    figure = plt.figure()
    subplot = figure.add_subplot(111)
    plots = []
    for i in xrange(numTasks):    
        plots.append(subplot.plot(epochs[0:len(rewards[i])], rewards[i], label="Task: " + str(i)))
 
    # L = subplot.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=numTasks / 4, fancybox=True, shadow=True)
    # L.draggable(state=True)
    figure.suptitle(title)
 
    plt.xlabel('epochs')
    plt.ylabel('Average Reward')
    # plt.show()
 
 
def plotResults(filename, title, resultsFileType = 0):
    resFile = open(filename, 'r')
    line = resFile.readline()
    rewards = []
 
    if resultsFileType == 2:
        rewards.append([])
        rewards.append([])
 
    epochs  = []
    while  line != "":
        line = resFile.readline()
        if line == '\n' or line == '':
            continue
 
        contents = line.split(",")
        if resultsFileType == 0:
            if len(contents) > 3:
                epochs.append(contents[0])
                rewards.append(contents[3])
        elif resultsFileType == 1:
            if len(contents) > 1:
                epochs.append(contents[0])
                rewards.append(contents[1])
        elif resultsFileType == 2:
            if len(contents) > 1:
                rewards[0].append(contents[1])
                rewards[1].append(contents[2])
                epochs.append(contents[0])
 
    figure = plt.figure()
    subplot = figure.add_subplot(111)
 
    if resultsFileType == 2:
        subplot.plot(epochs, rewards[0])
        subplot.plot(epochs, rewards[1])
    else:
        subplot.plot(epochs, rewards)
 
    figure.suptitle(title)
 
    plt.xlabel('epochs')
    plt.ylabel('Average Reward')
    # subplot.title(title)
   
 
def main(game=""):
    #plotResults('freewayEasy.txt', 'Freeway Easy Mode', 0)
    #plotResults('freewayHard.txt', 'Freeway Hard Mode', 1)
    #plotResults('pong1.txt', 'Pong', 1)
    # plotResults('freeway2diff.txt', 'Freeway 2 Hard and Easy', 2)
 
    if game == "boxing":
        t = 4
    elif game == "hero":
        t = 5
    elif game == "space_invaders":
        t = 32
    elif game == "freeway":
        t = 16
    elif game == "crazy_climbers":
        t = 8
    elif game =="pong,breakout":
        t = 2
    elif game == "space_invaders,demon_attack":
        t = 2
    elif game == "robotank,battlezone":
        t = 2
    else:
        t = 1
 
 
    # plotMultiGameTaskResults("multiGameResults/", game, 2)
 
    # plotMultiFlavorResults("freewayFlavorForMike/resultsOnly/", 16)
    plotMultiFlavorResults("boxingFlavorForMike/resultsOnly/", "Boxing", 4)
 
    # resultsString = "results.csv"
    # plotTaskResults("seededResults/"+ game + "/fullShare/" + resultsString, game + " Full Share", t)
    # plotTaskResults("seededResults/"+ game + "/layerShare/" + resultsString, game + " Layer Share", t)
    # plotTaskResults("seededResults/"+ game + "/representationShare/" + resultsString, game +" Representation Share", t)
    # plt.show()
 
 
if __name__=="__main__":
    main()