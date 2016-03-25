import os
from shutil import copyfile
import shutil
import re

def findBestEpochsOfResultsFile(inputfile):
    f = open(inputfile, 'r')
    header = f.readline()
    firstLine = f.readline()
    
    if header == "" or header == "\n":
        return None, None

    if firstLine == "" or firstLine == "\n":
        return None, None

    firstLineContents = [item.strip() for item in firstLine.split(',')]
    
    bestEpoch = int(firstLineContents[0])
    bestValue = float(firstLineContents[3])

    for line in f:
        if re.search("[a-zA-Z]", line) != None:
            continue
        line.split(',')
        lineContents = [item.strip() for item in line.split(',')]
        epoch = int(lineContents[0])
        value = float(lineContents[3])


        if value > bestValue:
            bestEpoch = epoch
            bestValue = value

    return bestEpoch, bestValue




def createGameFolders(projectDirectoryString, oldDir, newDir):
    folders = os.listdir(projectDirectoryString + oldDir)

    for folder in folders:
        gamePath = projectDirectoryString + newDir + folder
        if os.path.isdir(projectDirectoryString + oldDir + folder):
            os.makedirs(gamePath + "/seed_1/")





def createTransferBaselineJobFiles(baseDirectory = 0, gameList = 0, modeList= 0, diffList = 0):
    baseDirectory = "/gs/project/ntg-662-aa/RLRP/transferBaselines2/"
    gameList = ["boxing", "freeway", "hero", "space_invaders"]
    flavorList = [  [[0, 1], [0, 2], [0,3]], \
                    [[0, 1]], \
                    [[0, 1],[0, 2],[0, 3],[0, 4]], \
                    [[0,6], [0, 7]]
                ]

    seeds = [2]
    epochs = 200
    baseRomPath = "/home/rpost/roms/"
    for gameIndex in len(gameList):
        game = gameList[gameIndex]
        gamesFlavors = flavorList[gameIndex]
        for flavor in gamesFlavors:
            mode = flavor[0]
            diff = flavor[1]

            for seed in seeds:

                experimentDirectory = baseDirectory + "/" + str(game) + "/mode_" + str(mode) + "_diff_" + str(diff) + "/seed_" + str(seed) + "/"
                jobFilename = str(game) + "m_" + str(mode) + "_d_" + str(diff) + "_s_" + str(seed) + ".pbs"
                print experimentDirectory

                if not os.path.isdir(experimentDirectory):
                    os.makedirs(experimentDirectory)

                header = createPBSHeader(experimentDirectory)
                theanoFlag = createTheanoFlagString("gpu")
                command = createJobCommandString(experimentDirectory, game, seed, epochs, baseRomPath, str(mode), str(diff)):

                jobFile = open(experimentDirectory + jobFilename)
                jobFile.write(header + "\n\n" + theanoFlag + " " + command)
                jobFile.close()





def createPBSHeader(jobDirectory, walltime = "5:00:00:00"):
    text = "#PBS -S /bin/bash\n#PBS -A ntg-662-aa\n#PBS -l nodes=1:gpus=1\n#PBS -l walltime=" + walltime + "\n"
    text+= "#PBS -M rpost@cs.ualberta.ca\n#PBS -m n\n#PBS -t 1\n"
    text+= "#PBS -o " + jobDirectory + "jobOutput.txt\n"
    text+= "#PBS -e " + jobDirectory + "error.txt\n"

    return text


def createTheanoFlagString(device="gpu"):
    return "THEANO_FLAGS='device=%s,floatX=float32,optimizer_including=cudnn'" %(device)


def createJobCommandString(projectDirectoryString, rom, seed, epochs, baseRomPath, modeStr="", diffStr = ""):
    command = "python /home/rpost/RLRP/Base/runALEExperiment.py --networkType dnn " \
    + "--rom %s --baseRomPath %s " %(rom, baseRomPath) \
    + "--experimentDirectory %s " %(projectDirectoryString)  \
    + "--evaluationFrequency 1 --seed %s --numEpochs %s "%(seed, epochs) \
    + "--modeString %s --difficultyString %s " %(modeStr, diffStr)\
    + "> " + projectDirectoryString + "/experimentOutput.txt"
    return command

# def createEvaluationPBSFile(projectDirectoryString, romName, baseRomPath):
#     pbsContents = createPBSHeader(projectDirectoryString) + "\n" \
#                     + createPythonPathExportString() + "\n" \
#                     + createTheanoFlagString() \
#                     + createEvaluationJobCommandString(projectDirectoryString, romName, baseRomPath)

#     return pbsContents





#open directory full of game folders for a list of games
#open directory to contain dqn new baselines
#create folders/seed_1/ for each game
#copy best network file for that game into the new folder
#create the pbs file to run the evaluation job

# def createAllGameEvaluationPBSFiles(projectDirectoryString, oldDir, newDir, baseRomPath):
#     games = os.listdir(projectDirectoryString + oldDir)

#     gameFolders = map(lambda item: projectDirectoryString + newDir + item + "/seed_1/", games)

#     for game,folder in zip(games,gameFolders):
        
#         if not os.path.isdir(folder):
#             continue

#         fileContents = createEvaluationPBSFile(folder, game, baseRomPath)
#         outputFile = open(folder + game + ".pbs", "w")
#         outputFile.write(fileContents)
#         outputFile.close()



def createAllGameBestEvalNetworkFile(projectDirectoryString, oldDir, newDir):
    games = os.listdir(projectDirectoryString + oldDir)
    oldGameFolders = map(lambda item: projectDirectoryString + oldDir + item + "/seed_1/", games)    
    newGameFolders = map(lambda item: projectDirectoryString + newDir + item + "/seed_1/", games)


    for game, oldGameFolder, newGameFolder in zip(games, oldGameFolders, newGameFolders):
        if not os.path.isdir(oldGameFolder):
            continue

        bestEpoch, bestValue = findBestEpochsOfResultsFile(oldGameFolder + "results.csv")
        print "Game: " + game + " has best evaluation of:" + str(bestValue) + " on epoch: " + str(bestEpoch)

        bestNetworkFile = oldGameFolder + "network_" + str(bestEpoch + 1) + ".pkl"
        
        epochFile = open(oldGameFolder + "bestEpochNum: "+ str(bestEpoch) + ".txt")
        
        epochFile.write("Epoch: %s\n" % str(bestEpoch))
        epochFile.write("Value: %s\n" % str(bestValue))
        epochFile.close()

        copyfile(bestNetworkFile, newGameFolder + "evaluationNetwork.pkl")


#Pass in a rom directory - names of roms with .bin ending are extracted and returned in a list
def getGameList(directory):
    gameFolders = os.listdir(directory)
    gameList = []
    for folder in gameFolders:
        if folder.endswith(".bin"):
            gameList.append(folder[0:-4])

    return gameList

def copyGameFoldersToNewDirectory(romDirectory, originalDirectory, newDirectory):
    gameList = getGameList(romDirectory)
    foldersToMove = os.listdir(originalDirectory)
    
    #"/gs/project/ntg-662-aa/dqn_baselinesDebug/"
    print gameList
    print foldersToMove

    for folderToMove in foldersToMove:
        for game in gameList:
            if game in folderToMove:
                print folderToMove
		print newDirectory + str(game) + "/seed_1/"
		shutil.move(originalDirectory + folderToMove, newDirectory + str(game) + "/seed_1/")
                break


def deleteMostRecentNetworkFile(romDirectory, projectDirectory):
    gameFolders = os.listdir(projectDirectory)
    for gameFolder in gameFolders:
        if not os.path.isdir(projectDirectory + gameFolder + "/seed_1/"):
            continue

        gameFolderContents = os.listdir(projectDirectory + gameFolder + "/seed_1/")
        gamesNetworkFiles = [item for item in gameFolderContents if "network" in item]
        networkNumbers = [int(item[item.index("_") + 1 : item.index(".")]) for item in gamesNetworkFiles]
        highestNum = max(networkNumbers)
        fileToRemove = projectDirectory + gameFolder + "/seed_1/network_" + str(highestNum) + ".pkl"
        print fileToRemove

        os.remove(fileToRemove)




def getBestResultsList(romDirectory, projectDirectory, extensionToResults):
    gameList = getGameList(romDirectory)
    projectDirectoryContents = os.listdir(projectDirectory)
    gameDict = {}
    for folder in projectDirectoryContents:
        fullPath = projectDirectory + folder + "/" + extensionToResults
        print fullPath
        if not os.path.isfile(fullPath):
            continue

        result = findBestEpochsOfResultsFile(fullPath)
        gameDict[folder] = result



    for key in sorted(gameDict.keys()):
        # print str(key) + ",\t" + str(gameDict[key][1])
        # print '{0:{width}}'.format(\

        print str(gameDict[key][1])
        #print '{:<25}'.format(str(key) + ",") + str(gameDict[key][1])



def getCompiledResultsFolder(projectDirectoryString, outputPath):
    #get list of games, project directory and extension to files create folders to hold only the task results files
    resFiles = []
    for root, subdirs, files in os.walk(projectDirectoryString):
        for file in files:
            if 'result' in file and file.endswith(".csv"):
                resFiles.append(root + "/" + file)
    splitFileName = [f.split("/") for f in resFiles]
    for file in splitFileName:
        newPath = outputPath + "/" + file[-3] + "/" + file[-2]
        if not os.path.isdir(newPath):
            os.makedirs(newPath)
        fileToCopy = "/".join(file[1:])#file[1] + "/" + file[2] + "/" + file[3]
        newFilename = newPath + "/" + file[-1]
        print fileToCopy
        print newFilename
        # copyfile(fileToCopy, newFilename)

        # copyfile(projectDirectoryString + "/" + file[1] + "/" + file[2] + "/" + file[3], newPath + "/" + file[3])


def main():
    environment = "guillimin"
    if environment == "home":
        projectDirectoryString = "/home/robpost/Desktop/MiscScripts/"
        oldDir = "pullBestEpoch/"
        newDir = "newFiles/"
        baseRomPath = "/home/robpost/Desktop/ALE/roms/"
    elif environment == "guillimin":
        projectDirectoryString = "/gs/project/ntg-662-aa/"
        oldDir = "dqn_baselines/"
        newDir = "dqn_baselinesDebug/"
        baseRomPath = "/home/rpost/roms"
    
    #createGameFolders(               projectDirectoryString, oldDir, newDir)
    #createAllGameBestEvalNetworkFile(projectDirectoryString, oldDir, newDir)
    #createAllGameEvaluationPBSFiles( projectDirectoryString, oldDir, newDir, baseRomPath)

    # copyGameFoldersToNewDirectory(baseRomPath, "/home/rpost/", projectDirectoryString + newDir)
    # deleteMostRecentNetworkFile(baseRomPath, projectDirectoryString + "dqnNewBaselines/")


    # getBestResultsList(baseRomPath, projectDirectoryString + "dqnNewBaselines/", "seed_1/results.csv")
    createTransferBaselineJobFiles()
    # getBestResultsList(baseRomPath, projectDirectoryString + "dqnNewBaselines/", "seed_1/results.csv")

if __name__ == "__main__":
    main()
