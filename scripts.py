import os
from shutil import copyfile
import shutil
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
    bestValue = float(firstLineContents[1])

    for line in f:
        line.split(',')
        lineContents = [item.strip() for item in line.split(',')]
        epoch = int(lineContents[0])
        value = float(lineContents[1])


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




def createPBSHeader(jobDirectory):
    text = """
#PBS -S /bin/bash
#PBS -A ntg-662-aa
#PBS -l nodes=1:gpus=1,mem=12gb
#PBS -l walltime=03:00:00
#PBS -M rpost@cs.ualberta.ca
#PBS -m n
#PBS -t 1\n""" + \
        "#PBS -o " + jobDirectory + "output.txt\n" + \
        "#PBS -e " + jobDirectory + "error.txt\n"

    return text

def createPythonPathExportString():
    return """
export PYTHONPATH=/home/rpost/DeepRL/agents/:$PYTHONPATH
export PYTHONPATH=/home/rpost/DeepRL/utilities/:$PYTHONPATH
export PYTHONPATH=/home/rpost/DeepRL/network/:$PYTHONPATH
    """

def createTheanoFlagString():
    return "THEANO_FLAGS='device=gpu,floatX=float32,optimizer_including=cudnn,dnn.conv.algo_fwd=time_once,dnn.conv.algo_bwd=time_once' "


def createEvaluationJobCommandString(projectDirectoryString, romString, baseRomPath):
    return "python /home/rpost/DeepRL/run_dqtn.py --network-type dnn " \
    + "--rom %s --base-rom-path %s " %(romString, baseRomPath) \
    + "--nn-file %s " %( projectDirectoryString + "evaluationNetwork.pkl")  \
    + "--evaluationFrequency 1 --seed 1 --epochs 2 --deathEndsEpisode " \
    + "--numHoldoutQValues %s " %("32") \
    + "--steps-per-epoch 0 " \
    + "> " + projectDirectoryString + "experimentOutput.txt"

def createEvaluationPBSFile(projectDirectoryString, romName, baseRomPath):
    pbsContents = createPBSHeader(projectDirectoryString) + "\n" \
                    + createPythonPathExportString() + "\n" \
                    + createTheanoFlagString() \
                    + createEvaluationJobCommandString(projectDirectoryString, romName, baseRomPath)

    return pbsContents





#open directory full of game folders for a list of games
#open directory to contain dqn new baselines
#create folders/seed_1/ for each game
#copy best network file for that game into the new folder
#create the pbs file to run the evaluation job

def createAllGameEvaluationPBSFiles(projectDirectoryString, oldDir, newDir, baseRomPath):
    games = os.listdir(projectDirectoryString + oldDir)

    gameFolders = map(lambda item: projectDirectoryString + newDir + item + "/seed_1/", games)

    for game,folder in zip(games,gameFolders):
        
        if not os.path.isdir(folder):
            continue

        fileContents = createEvaluationPBSFile(folder, game, baseRomPath)
        outputFile = open(folder + game + ".pbs", "w")
        outputFile.write(fileContents)
        outputFile.close()



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
        for game in gameList:
            if not os.path.isfile(folder + extensionToResults):
                continue

            result = findBestEpochsOfResultsFile(folder + extensionToResults)
            gameDict[game] = result


    for key in gameDict:
        print gameDict[key]



def main():
    environment = "guillimin"
    if environment == "home":
        projectDirectoryString = "/home/robpost/Desktop/scripts/"
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
    deleteMostRecentNetworkFile(baseRomPath, projectDirectoryString + "dqnNewBaselines/")

main()
