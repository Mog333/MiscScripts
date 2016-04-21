import os
from shutil import copyfile
import shutil
import re
import sys
import subprocess

archs = ["DQNNet", 
    "PolicySwitchNet", 
    "PolicyPartialSwitchNet", 
    "TaskTransformationNet",  
    "FirstRepresentationSwitchNet"
        ]


gamesNotDone = ["atlantis", "bank_heist","battle_zone","beam_rider","bowling","boxing","breakout","centipede","chopper_command","crazy_climber","demon_attack","double_dunk","enduro","fishing_derby","freeway","frostbite","gopher","gravitar","hero","ice_hockey","ms_pacman","name_this_game","phoenix","pong","private_eye","riverraid","road_runner","robotank","tennis","tutankham","up_n_down","video_pinball","wizard_of_wor","zaxxon"]


def copytest(gamename):
    for arch in archs:
        for file in os.listdir("./" + arch):
            if "task" in file and ".csv" in file:
                filepath = "./" + arch + "/" + file
                newfilepath = "../../../resultsCompile1/" + gamename + "/"+ arch + "/" + file
                print filepath
                print newfilepath 
                copyfile(filepath, newfilepath)



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
    lastEpoch = bestEpoch

    for line in f:
        if re.search("[a-zA-Z]", line) != None:
            continue
        line.split(',')
        lineContents = [item.strip() for item in line.split(',')]
        epoch = int(lineContents[0])
        value = float(lineContents[3])
        lastEpoch = epoch

        if value > bestValue:
            bestEpoch = epoch
            bestValue = value

    return bestEpoch, bestValue, lastEpoch




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
    for gameIndex in range(len(gameList)):
        game = gameList[gameIndex]
        gamesFlavors = flavorList[gameIndex]
        for flavor in gamesFlavors:
            mode = flavor[0]
            diff = flavor[1]

            for seed in seeds:

                experimentDirectory = baseDirectory + "/" + str(game) + "/mode_" + str(mode) + "_diff_" + str(diff) + "/seed_" + str(seed) + "/"
                jobFilename = str(game) + "_m_" + str(mode) + "_d_" + str(diff) + "_s_" + str(seed) + ".pbs"
                print experimentDirectory

                if not os.path.isdir(experimentDirectory):
                    os.makedirs(experimentDirectory)

                header = createPBSHeader(experimentDirectory)
                theanoFlag = createTheanoFlagString("gpu")
                command = createJobCommandString(experimentDirectory, game, seed, epochs, baseRomPath, str(mode), str(diff))

                jobFile = open(experimentDirectory + jobFilename, "w")
                jobFile.write(header + "\n\n" + theanoFlag + " " + command)
                jobFile.close()

# scripts.createExperimentLayout("/home/robpost/Desktop/MiscScripts/test/", "/home/robpost/Desktop/Research/ALE/roms", ["freeway", "assault,demon_attack"], [[('0','0'), ('0','1')],[('0;0','0;0')]], ["DQNNet", "PolicySwitchNet", "FirstRepresentationSwitchNet"], [1,2,3], "3:00:00:00", 100)
def createExperimentLayout(baseDirectory, baseRomPath, gameList, flavorList, architectureList, seedList, walltime = "4:00:00:00", epochs = 200, createBaseline = False, deviceString="gpu"):
    #gameList is a list of strings - each is a game or list of games
    #flavorList is a list of lists, one for each game, list elements are tuples with two elements, mode and diff strings
    #architectureList is a list of strings - one for each architecture to get run
    #createBaseline is a bool - to create the baseline job files or not

    #For each game in gamelist we will create a folder for that game/romstring
    #inside are folders of format M~_D~ for each mode/diff string used 
    #inside are folders for each architecture we wish to run this experiment with
    #Inside the architecture folder is some number of seed folders
    #Each seed folder is a project directory

    #gameList: ["space_invaders,assault", "pong,breakout"]
    #flavorString: [[('0;0', '0;0'), ('0,7;0', '0;0')],[('0;0', '0;0')]]

    # archs = ["DQNNet", "PolicySwitchNet", "FirstRepresentationSwitchNet"]

    gameIndex = 0
    for game in gameList:
        gameDir = baseDirectory + "/" + game
        if not os.path.exists(gameDir):
            os.makedirs(gameDir)
        flavors = flavorList[gameIndex]

        for flavor in flavors:
            modeString = flavor[0]
            diffString = flavor[1]
            flavorDir = baseDirectory + "/" + game + "/M" + modeString + "_D" + diffString
            if not os.path.exists(flavorDir):
                os.makedirs(flavorDir)
            for architecture in architectureList:
                archDir = baseDirectory + "/" + game + "/M" + modeString + "_D" + diffString + "/" + architecture
                if not os.path.exists(archDir):    
                    os.makedirs(archDir)

                for seed in seedList:
                    projectDirectory = baseDirectory + "/" + game + "/M" + str(modeString) + "_D" + str(diffString) + "/" + architecture + "/seed_" + str(seed) + "/"
                    if not os.path.exists(projectDirectory):
                        os.makedirs(projectDirectory)
                    jobFilename = str(game) + "_m_" + str(modeString) + "_d_" + str(diffString) + "_s_" + str(seed) + ".pbs"

                    header = createPBSHeader(projectDirectory, walltime)
                    theanoFlag = createTheanoFlagString(deviceString)
                    command = createJobCommandString(projectDirectory, game, seed, epochs, baseRomPath, modeString, diffString)

                    jobFile = open(projectDirectory + jobFilename, "w")
                    jobFile.write(header + "\n\n" + theanoFlag + " " + command)
                    jobFile.close()


        gameIndex += 1


def createPBSHeader(jobDirectory, walltime = "5:00:00:00"):
    text = "#PBS -S /bin/bash\n#PBS -A ntg-662-aa\n#PBS -l nodes=1:gpus=1\n#PBS -l walltime=" + walltime + "\n"
    text+= "#PBS -M rpost@cs.ualberta.ca\n#PBS -m bea\n"#PBS -t 1\n"
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

        #print str(gameDict[key][1])
        print '{:<25}'.format(str(key) + ",") + str(gameDict[key][1]) + " at epoch: " + str(gameDict[key][0]) +str(". highest epoch: ")+ str(gameDict[key][2])
    print "Games not complete"
    for key in sorted(gameDict.keys()):
        if gameDict[key][2] < 200:
            print key



def runJobs(projectDirectory, allowedList = None):
    p = subprocess.Popen(['find', projectDirectory, '-name', '*.pbs'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = p.communicate()
    pbsList = out.split('\n')[0:-1]
    print pbsList
    for jobFileString in pbsList:
        if allowedList != None and jobFileString.split("/")[4] in allowedList:
            print jobFileString

            with open(jobFileString, "r") as f:
                contents = f.readlines()
            newFile = ""
            for line in contents:
                if "walltime" in line:
                    newFile += "#PBS -l walltime=3:00:00:00\n"
                else:
                    newFile += line

            print newFile
            with open(jobFileString, "w") as f:
                f.write(newFile)
            p2 = subprocess.Popen(["qsub", jobFileString], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out2,err2=p2.communicate()
            print out2

def getCompiledResultsFolder(projectDirectoryString, outputPath):
    #get list of games, project directory and extension to files create folders to hold only the task results files
    resFiles = []
    for root, subdirs, files in os.walk(projectDirectoryString):
        for file in files:
            if 'result' in file and file.endswith(".csv"):
                fullResultsPath = root + "/" + file
                endOffullResultsPath = fullResultsPath.replace(projectDirectoryString, "")
                resFiles.append(endOffullResultsPath)

    for file in resFiles:
    	print "file:\t"+file
        newPath = outputPath + "/" file[0:file.rfind("/")]
        print "newpath:\t" + newPath
        if not os.path.isdir(newPath):
            os.makedirs(newPath)
        fileToCopy = projectDirectoryString + "/" + file
        newFilename = outputPath + "/" + file
        print "filetocopy:\t"+fileToCopy
        print "newfilename:\t"+newFilename
        # copyfile(fileToCopy, newFilename)



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
    # createTransferBaselineJobFiles()
    # getBestResultsList(baseRomPath, projectDirectoryString + "dqnNewBaselines/", "seed_1/results.csv")

    createExperimentLayout(
        "/gs/project/ntg-662-aa/RLRP/transfer3", 
        "/home/rpost/roms", 
        ["assault,demon_attack,space_invaders,phoenix", "enduro,demon_attack,pong,space_invaders", "enduro,pong,gopher,space_invaders"], 
        [[('0;0;0;0','0;0;0;0')], [('0;0;0;0','0;0;0;0')], [('0;0;0;0','0;0;0;0')]] 
        ["DQNNet", "PolicySwitchNet", "FirstRepresentationSwitchNet"], 
        [1,2,3,4,5], 
        "4:00:00:00", 200)

    '''
    createExperimentLayout(
        "/gs/project/ntg-662-aa/RLRP/baselines3/", 
        "/home/rpost/roms", 
        ["assault","demon_attack","space_invaders","phoenix","enduro","pong","gopher"], 
        [[('0','0')], [('0','0')], [('0','0')], [('0','0')], [('0','0')], [('0','0')], [('0','0')]]
        ["DQNNet"], 
        [1,2,3,4,5], 
        "4:00:00:00", 100)
    '''

if __name__ == "__main__":
    main()
