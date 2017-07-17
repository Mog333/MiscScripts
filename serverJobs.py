import sys
import os

def createPBSHeader(jobDirectory, walltime = "5:00:00:00"):
    text = "#PBS -S /bin/bash\n#PBS -A ntg-662-aa\n#PBS -l nodes=1:gpus=1\n#PBS -l walltime=" + walltime + "\n"
    text+= "#PBS -M rpost@cs.ualberta.ca\n#PBS -m bea\n"#PBS -t 1\n"
    text+= "#PBS -o '" + jobDirectory + "jobOutput.txt'\n"
    text+= "#PBS -e '" + jobDirectory + "error.txt'\n"

    return text


def createTheanoFlagString(device="gpu", includeCUDNN = True):
    flagString = "THEANO_FLAGS='device=%s,floatX=float32" % (device)
    if includeCUDNN:
        flagString += ",optimizer_including=cudnn'"
    else:
        flagString += "'"

    return flagString


def createJobCommandString(baseRomPath, jobScriptPath, projectDirectoryString, romString, networkType, seed, epochs, outputFile = "commandOutput.txt", otherOptions = []):
    # /home/rpost/RLRP/Base/runALEExperiment.py
    '''
    Arguments:

        baseRomPath:    (string)
            directory string where ALE roms are located

        jobScriptPath:  (string)
            Path to a python script to be run (runALEExperiment.py)

        projectDirectoryString: (string)
            directory string for the experiment

        romString: (string)
            string for the roms and rom options to be be used

        seed: (int)
            seed to use for experiment

        epochs: (int)
            number of epochs to run the experiment for

        outputFile: (string)    Default: "commandOutput.txt"
            filename to write the output from the command to

        otherOptions: (list of string) Default:[]
            other string options to append to the job command
            ex: ["--evaluationFrequency 2", "--actionSet full"]

    Returns:
        a job command string

    Description:
        builds a job command string from the given parameters

    '''


    command = "python " + jobScriptPath + " --networkType %s " %(networkType)
    command += "--rom '%s' --baseRomPath %s " %(romString, baseRomPath)
    command += "--experimentDirectory '%s' " %(projectDirectoryString)
    command += "--seed %s --numEpochs %s " %(seed, epochs)

    for commandOption in otherOptions:
        command += " " + commandOption

    command += " > '" + projectDirectoryString + "/" + outputFile + "'"
    
    return command




def createExperimentLayout(baseDirectory, baseRomPath, jobScriptPath, gameList, architectureList, seedList, networkType='dnn', walltime = "4:00:00:00", epochs = 200, deviceString="gpu", forceCUDNN = False, jobOptions = []):
    '''
    Arguments:
        baseDirectory:  (string)
            directory string where to create the experiment layout
        
        baseRomPath:    (string)
            directory string where ALE roms are located

        jobScriptPath:  (string)
            path to a python executable job file 
        
        gameList:       (list of strings)
            list of rom strings

        architectureList:(List of strings)
            list of architectures each one is a separate experiment

        seedList:       (list of ints)
            list of seeds one for each separate experiment

        networkType:    (string)
            specify to use 'conv' or 'dnn' for network layer type

        walltime:       (string)
            string for maximum amount of time to run experiment for

        epochs:         (int)
            integer number of epochs to run each experiment for

        deviceString:   (string)
            string for either gpu or cpu usage

        forceCUDNN:     (boolean)
            Bool to force theano to use cudnn libraries or throw an exception if it cant.

        otherOptions:   (string list)
            list of options to be passed into the job command string. ex: ['--stepsPerTrainingEpoch 100000'] 

    Returns:
        None

    Exceptions:
        File / IO error if unable to create folders / file

    Description:
        Creates a experiment layout of job files / directories
        The result is a tree like structure
        Each game folder contains all the specified architecture folders
        Each architecture folder contains all the specified seed folders
        Seed folders are the final project directory containing a job file
        All experiments get the same walltime / epochs


    Example:

    createExperimentLayout(
        "/gs/project/ntg-662-aa/RLRP/transfer3",
        "/home/rpost/roms",
        "/home/rpost/RLRP/base/runALEExperiment.py",
        ["assault^demon_attack^space_invaders^phoenix", "enduro^demon_attack^pong^space_invaders", "enduro^pong^gopher^space_invaders"], 
        ["DQNNet", "PolicySwitchNet", "FirstRepresentationSwitchNet"], 
        [1,2,3,4,5], 'conv',
        "4:00:00:00", 200, "gpu", False, ['--stepsPerTrainingEpoch 100000'])


    '''
createExperimentLayout( "/gs/project/ntg-662-aa/AlternateDQN",  "/home/rpost/roms", "/home/rpost/RLRP/base/runALEExperiment.py", ["space_invaders", "pong", "freeway","breakout"], ["DQNAlternateNet", "DQNAlternate2Net"], [1], 'dnn', "4:00:00:00", 100, "gpu", True)
    gameIndex = 0
    for game in gameList:
        gameDir = baseDirectory + "/" + game
        if not os.path.exists(gameDir):
            os.makedirs(gameDir)

        for architecture in architectureList:
            if "--disjointDQN True" in jobOptions:
                archDir = gameDir + "/" + "disjoint"+ architecture
            else:
                archDir = gameDir + "/" + architecture
            if not os.path.exists(archDir):    
                os.makedirs(archDir)

            for seed in seedList:
                projectDirectory = archDir + "/seed_" + str(seed) + "/"
                if not os.path.exists(projectDirectory):
                    os.makedirs(projectDirectory)
                if "--disjointDQN True" in jobOptions:
                    jobFilename = str(game) + "_a_disjoint" + architecture + "_s_" + str(seed) + ".pbs"
                else:
                    jobFilename = str(game) + "_a_" + architecture + "_s_" + str(seed) + ".pbs"

                header     = createPBSHeader(projectDirectory, walltime)
                theanoFlag = createTheanoFlagString(deviceString, forceCUDNN)
                command    = createJobCommandString(baseRomPath, jobScriptPath, projectDirectory, game, networkType, seed, epochs, outputFile = "commandOutput.txt", otherOptions = jobOptions)

                jobFile = open(projectDirectory + jobFilename, "w")
                jobFile.write(header + "\n\n" + theanoFlag + " " + command)
                jobFile.close()


        gameIndex += 1



def main(args):
    #createExperimentLayout( "/home/robpost/Desktop/Research/MiscScripts/test",  "/home/robpost/Desktop/ALE/roms", "/home/robpost/Desktop/Research/RLRP/base/runALEExperiment.py", ["assault^demon_attack^space_invaders:(0,0)#(1,7)"], ["DQNNet", "PolicySwitchNet", "FirstRepresentationSwitchNet"], [1,2], 'conv', "4:00:00:00", 200, "cpu", False, ['--disjointDQN True'])

    #createExperimentLayout( "/gs/project/ntg-662-aa/AlternateDQN",  "/home/rpost/roms", "/home/rpost/RLRP/Base/runALEExperiment.py", ["space_invaders", "pong", "freeway","breakout"], ["DQNAlternateNet", "DQNAlternate2Net"], [1], 'dnn', "4:00:00:00", 100, "gpu", True)
    #createExperimentLayout( "/gs/project/ntg-662-aa/20EpochTransfer",  "/home/rpost/roms", "/home/rpost/RLRP/Base/runALEExperiment.py", ["assault^demon_attack^space_invaders", "enduro^pong^gopher^space_invaders", "enduro^demon_attack^pong^space_invaders"], ["DQNNet", "PolicySwitchNet", "FirstRepresentationSwitchNet"], [1,2,3,4,5,6,7,8,9,10], 'dnn', "1:00:00:00", 20, "gpu", True)
    #createExperimentLayout( "/gs/project/ntg-662-aa/AlternateDQN",  "/home/rpost/roms", "/home/rpost/RLRP/base/runALEExperiment.py", ["space_invaders", "pong", "freeway","breakout"], ["DQNAlternateNet", "DQNAlternate2Net"], [1], 'dnn', "4:00:00:00", 100, "gpu", True)
    

    createExperimentLayout( "/gs/project/ntg-662-aa/20EpochTransfer",  "/home/rpost/roms", "/home/rpost/RLRP/Base/runALEExperiment.py", ["assault^demon_attack^space_invaders", "enduro^pong^gopher^space_invaders", "enduro^demon_attack^pong^space_invaders"], ["DQNNet"], [1,2,3,4,5,6,7,8,9,10], 'dnn', "2:00:00:00", 20, "gpu", True, [])


if __name__ == "__main__":
    main(sys.argv[1:])
















    ###
    #OLD Flavor Usage
    ###

    # gameIndex = 0
    # for game in gameList:
    #     gameDir = baseDirectory + "/" + game
    #     if not os.path.exists(gameDir):
    #         os.makedirs(gameDir)
    #     flavors = flavorList[gameIndex]

    #     for flavor in flavors:
    #         modeString = flavor[0]
    #         diffString = flavor[1]
    #         flavorDir = baseDirectory + "/" + game + "/M" + modeString + "_D" + diffString
    #         if not os.path.exists(flavorDir):
    #             os.makedirs(flavorDir)
    #         for architecture in architectureList:
    #             archDir = baseDirectory + "/" + game + "/M" + modeString + "_D" + diffString + "/" + architecture
    #             if not os.path.exists(archDir):    
    #                 os.makedirs(archDir)

    #             for seed in seedList:
    #                 projectDirectory = baseDirectory + "/" + game + "/M" + str(modeString) + "_D" + str(diffString) + "/" + architecture + "/seed_" + str(seed) + "/"
    #                 if not os.path.exists(projectDirectory):
    #                     os.makedirs(projectDirectory)
    #                 jobFilename = str(game) + "_m_" + str(modeString) + "_d_" + str(diffString) + "_s_" + str(seed) + ".pbs"

    #                 header = createPBSHeader(projectDirectory, walltime)
    #                 theanoFlag = createTheanoFlagString(deviceString)
    #                 command = createJobCommandString(projectDirectory, game, seed, epochs, baseRomPath, modeString, diffString)

    #                 jobFile = open(projectDirectory + jobFilename, "w")
    #                 jobFile.write(header + "\n\n" + theanoFlag + " " + command)
    #                 jobFile.close()


    #     gameIndex += 1


