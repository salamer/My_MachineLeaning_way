from numpy import *

def loadDataSet():
    dataMat=[]
    labelMat=[]
    fr=open("testSet.txt")
    for line in fr.readlines():
        lineArr=line.strip().split()
        dataMat.append([1.0,float(lineArr[0]),float(lineArr[1])])
        labelMat.append(int(lineArr[2]))

    return dataMat,labelMat

def sigmoid(inX):

    return 1.0/(1+exp(-inX))


def gradAscent(dataMatIn,classLabels):
    dataMatrix=mat(dataMatIn)
    labelMat=mat(classLabels).transpose()
    m,n=shape(dataMatrix)
    alpha=0.001
    maxCycle=1000
    weights=ones((n,1))

    weight_data1=[]
    weight_data2=[]
    weight_data3=[]

    for k in range(maxCycle):
        h=sigmoid(dataMatrix*weights)

        print h

        error=(labelMat-h)
#        print error

        weights=weights+alpha*dataMatrix.transpose()*error
    '''

        weight_data1.append(float(weights[0]))
        weight_data2.append(float(weights[1]))
        weight_data3.append(float(weights[2]))
    import matplotlib.pylab as plt
    import seaborn as sns

    plt.plot(arange(maxCycle),weight_data1,c="red",alpha=0.6)
    plt.plot(arange(maxCycle),weight_data2,c="pink",alpha=0.6)
    plt.plot(arange(maxCycle),weight_data3,c="purple",alpha=0.6)
    plt.show()
    '''

    return weights

def plotBestFit(weights):
    import matplotlib.pylab as plt
    import seaborn as sns

    dataMat,labelMat=loadDataSet()
    dataArr=array(dataMat)
    n=shape(dataArr)[0]
    xcord1=[]
    ycord1=[]
    xcord2=[]
    ycord2=[]

    for i in range(n):
        if int(labelMat[i])==1:
            xcord1.append(dataArr[i,1])
            ycord1.append(dataArr[i,2])
        else:
            xcord2.append(dataArr[i,1])
            ycord2.append(dataArr[i,2])

#    fig=plt.figure

    plt.scatter(xcord1,ycord1,s=30,c="red",marker="s",label="X1")
    plt.scatter(xcord2,ycord2,s=30,c="green",label="X2")
    x=arange(-3.0,3.0,0.1)
    y=(-float(weights[0])-float(weights[1])*x)/float(weights[2])
    plt.plot(x,y,c="purple",label="fitted line")
    plt.legend()
    plt.xlabel("X1")
    plt.ylabel("X2")
    plt.show()

def stocGradAscent0(dataMatrix,classLabels):
    m,n=shape(dataMatrix)
    alpha=0.01
    weights=ones(n)
    for i in range(m):
        h=sigmoid(sum(dataMatrix[i]*weights))
        error=classLabels[i]-h
        weights=weights+alpha*error*dataMatrix[i]

    return weights


def stocGradAscent1(dataMatrix,classLabels,numIter=150):
    m,n=shape(dataMatrix)
    weights=ones(n)
    for j in range(numIter):
        dataIndex=range(m)
        for i in range(m):
            alpha=4/(1.0+j+i)+0.01
            randIndex=int(random.uniform(0,len(dataIndex)))
            h=sigmoid(sum(dataMatrix[randIndex]*weights))
            error=classLabels[randIndex]-h
            weights=weights+alpha*error*dataMatrix[randIndex]
            del(dataIndex[randIndex])
    return weights

def classifyVector(inX,weights):
    prob=sigmoid(sum(inX*weights))
    if prob>0.5:
        return 1.0
    else:
        return 0.0

def colicTest():
    frTrain=open('horseColicTrainning.txt')
    frTest=open("horseColicTest.txt")
    trainingSet=[]
    trainingLabel=[]
    for line in frTrain.readlines():
        currLine=line.strip().split('\t')
        lineArr=[]
        for i in range(21):
            lineArr.append(float(currLine[i]))
        trainingSet.append(lineArr)
        trainingLabel.append(float(currLine[21]))

    trainWeights=stocGradAscent1(array(trainingSet),trainingLabel,500)
    errorCount=0;
    numTestVec=0.0
    for line in frTest.readlines():
        numTestVec+=1.0
        currLine=line.strip().split('\t')
        lineArr=[]
        for i in range(21):
            lineArr.append(float(currLine[i]))

        if int(classifyVector(array(lineArr),trainWeights))!=int(currLine[21]):
            errorCount+=1

    errorRate=(float(errorCount)/numTestVec)
    print "the error rate of this test is : %f" % errorRate
    return errorRate

def multiTest():
    numTests=10
    errorSum=0.0
    for k in range(numTests):
        errorSum+=colicTest()

    print "after %d iterations the average error rate is %f " % (numTests,errorSum/float(numTests))
