# * This is an implementation of FLiDASH.
# * Copyright (C) 2019  Abhijit Mondal
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.



import os
import numpy as np
import matplotlib.pyplot as plt
import collections as cl
import sys

from util import load_trace
import util.videoInfo as video
from util.p2pnetwork import P2PNetwork
import util.randStateInit as randstate
from simenv.FLiDASH import FLiDASH
from simenv.Simple import Simple
from simenv.DHT import DHT
from simulator.simulator import Simulator
from util.group import GroupManager
from abr.FastMPC import AbrFastMPC
from abr.RobustMPC import AbrRobustMPC
from abr.BOLA import BOLA
from util.cdnUsages import CDN

AbrPensieve = None


RESULT_DIR = "./results/GenPlots"
BUFFER_LEN_PLOTS = "results/bufferlens"
STALLTIME_IDLETIME_PLOTS = "results/stall-idle"

def getPMF(x):
    x = [y for y in x]
    freq = list(cl.Counter(x).items())
    elements = zip(*freq)
    s = sum(elements[1])
    pdf = [(k[0],float(k[1])/s) for k in freq]
    # pdf.sort
    return pdf


def getCMF(elements):
    x = [y for y in elements]
    freq = list(cl.Counter(x).items())
    freq.sort(key = lambda x:x[0])
    x,y = zip(*freq)
    s = sum(y)
    cmf = [(p, float(sum(y[:i+1]))/s) for i, p in enumerate(x)]
    return cmf

def getCount(elements):
    x = [y for y in elements]
    freq = list(cl.Counter(x).items())
    freq.sort(key = lambda x:x[0])
    return freq
    x,y = zip(*freq)
    return x,y

def savePlotData(Xs, Ys, legend, pltTitle):
    dpath = os.path.join(RESULT_DIR, pltTitle.replace(" ", "_"))
    if not os.path.isdir(dpath):
        os.makedirs(dpath)
    fpath = os.path.join(dpath, legend + ".dat")
    with open(fpath, "w") as fp:
        assert len(Xs) == len(Ys)
        st = "\n".join(str(x) + "\t" + str(y) for x, y in zip(Xs, Ys))
        fp.write(st)

def restorePlotData(legend, pltTitle):
    dpath = os.path.join(RESULT_DIR, pltTitle.replace(" ", "_"))
    fpath = os.path.join(dpath, legend + ".dat")
    assert os.path.isfile(fpath)

    with open(fpath) as fp:
        Xs, Ys = list(zip(*[[float(x) for x in y.strip().split()] for y in fp]))
        return Xs, Ys

def plotStoredData(legends, _, pltTitle, xlabel):
#     plt.clf()
    plt.figure()
    pltData = []
    for name in legends:
        Xs, Ys = restorePlotData(name, pltTitle)
        pltData += [Xs, Ys]
        plt.plot(Xs, Ys, label=name)
    plt.legend(ncol = 2, loc = "upper center")
    plt.title(pltTitle)
    plt.xlabel(xlabel)

def findIgnorablePeers(results):
    p = set()
    for name, res in results.items():
        if name not in ["FLiDASH"]:
            continue
        for ag in res:
            if not ag._vGroup or ag._vGroup.isLonepeer(ag) or len(ag._vGroupNodes) <= 1:
                p.add(ag.networkId)
    return p

def plotAgentsData(results, attrib, pltTitle, xlabel, lonePeers = []):
    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 22}

    figsize=(7, 5)
    plt.clf()
    plt.rc('font', **font)
    plt.figure(figsize=figsize, dpi=150)
    assert min([len(res) for name, res in results.items()]) == max([len(res) for name, res in results.items()])
    pltData = {}
    for name, res in results.items():
        Xs, Ys = [], []
        for x, ag in enumerate(res):
            if ag.networkId in lonePeers:
                continue
            y = eval("ag." + attrib)
            Xs.append(x)
            Ys.append(y)

        savePlotData(Xs, Ys, name, pltTitle)
        pltData[name] = Ys
        Xs, Ys = list(zip(*getCMF(Ys)))
        savePlotData(Xs, Ys, name+"_cmf", pltTitle)
        plt.plot(Xs, Ys, label=name)
    plt.legend(ncol = 2, loc = "upper center")
    plt.title(pltTitle)
#     plt.xlabel(xlabel)
    dpath = os.path.join(RESULT_DIR, pltTitle.replace(" ", "_"))
#     x,l = plt.xticks()
#     plt.xticks(x, l, rotation=20)
    plt.savefig(dpath + "_cmf.eps", bbox_inches="tight")
    plt.savefig(dpath + "_cmf.png", bbox_inches="tight")
#     plt.show()
    plt.clf()
    plt.rc('font', **font)
    plt.figure(figsize=figsize, dpi=150)
    names, Yss = list(zip(*pltData.items()))
    plt.boxplot(Yss, labels=names, notch=True)
    plt.title(pltTitle)
    x,l = plt.xticks()
    plt.xticks(x, l, rotation=20)
    plt.savefig(dpath + "_box.png", bbox_inches="tight")
    plt.savefig(dpath + "_box.eps", bbox_inches="tight")

def plotCDNData(cdns):
    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 22}

    figsize=(7, 5)
    plt.clf()
    plt.rc('font', **font)
    plt.figure(figsize=figsize, dpi=150)
    pltData = {}
    pltTitle = "cdnUploaded"
    for name, res in cdns.items():
        Xs, Ys = list(zip(*res.uploaded))
        savePlotData(Xs, Ys, name, pltTitle)
        plt.plot(Xs, Ys, label=name)

        Xs, Ys = list(zip(*res.uploadRequests))
        savePlotData(Xs, Ys, name + "_cnt", pltTitle)

    plt.legend(ncol = 2, loc = "upper center")
    plt.title(pltTitle)
    dpath = os.path.join(RESULT_DIR, pltTitle.replace(" ", "_"))
    plt.savefig(dpath + "_cmf.eps", bbox_inches="tight")
    plt.savefig(dpath + "_cmf.png", bbox_inches="tight")

def measureBenefit(results, lonePeers):
    if "FLiDASH" not in results:
        return
    dags = {n.networkId:n for n in results["FLiDASH"]}
    RES_PATH = "./results/benefit/"
    for name, res in results.items():
        if name == "FLiDASH":
            continue
        ags = {n.networkId:n for n in res}
        benQoE = []
        benQ = []
        for n in ags:
            assert n in dags
            if n in lonePeers:
                continue
            qoep = ags[n]._vAgent.QoE
            qoed = dags[n]._vAgent.QoE
            benQoE.append((qoed - qoep)/abs(qoep))
            avqp = ags[n]._vAgent.avgBitrate
            avqd = dags[n]._vAgent.avgBitrate
            benQ.append((avqd - avqp)/abs(avqp))

        benQoEDir = os.path.join(RES_PATH, "QoE")
        if not os.path.isdir(benQoEDir):
            os.makedirs(benQoEDir)
        benQDir = os.path.join(RES_PATH, "bitrate")
        if not os.path.isdir(benQDir):
            os.makedirs(benQDir)

        with open(os.path.join(benQoEDir, name + ".dat"), "w") as fp:
            print(*benQoE, sep="\n", file = fp)
        with open(os.path.join(benQDir, name + ".dat"), "w") as fp:
            print(*benQ, sep="\n", file = fp)


GLOBAL_STARTS_AT = 5

def runExperiments(envCls, traces, vi, network, abr = BOLA, result_dir=None, modelPath = None):
    simulator = Simulator()
    grp = GroupManager(4, len(vi.bitrates)-1, vi, network)#np.random.randint(len(vi.bitrates)))

    deadAgents = []
    ags = []
    players = len(list(network.nodes()))
    idxs = [x%len(traces) for x in range(players)] #np.random.randint(len(traces), size=players)
    startsAts = np.random.randint(GLOBAL_STARTS_AT + 1, vi.duration/2, size=players)
    CDN.clear()
    for x, nodeId in enumerate(network.nodes()):
        idx = idxs[x]
        trace = traces[idx]
        startsAt = startsAts[x]
        env = envCls(vi = vi, traces = trace, simulator = simulator, grp=grp, peerId=nodeId, abr=abr, logpath=result_dir, modelPath=modelPath)
        simulator.runAt(startsAt, env.start, GLOBAL_STARTS_AT)
        ags.append(env)
    simulator.run()
    for i,a in enumerate(ags):
        assert a._vFinished # or a._vDead
    return ags, CDN.getInstance() #cdn is singleton, so it is perfectly okay get the instance

def main():
    global AbrPensieve
    allowed = ["BOLA", "FastMPC", "RobustMPC", "Penseiv", "DHTEnvironment", "FLiDASH"]
    if "-h" in sys.argv or len(sys.argv) <= 1:
        print(" ".join(allowed))
        return
    allowed = sys.argv[1:]
    if "Penseiv" in allowed and AbrPensieve is None:
        from abr.Pensiev import AbrPensieve as abp
        AbrPensieve = abp

    randstate.loadCurrentState()
    traces = load_trace.load_trace()
    vi = video.loadVideoTime("./videofilesizes/sizes_0b4SVyP0IqI.py")
    assert len(traces[0]) == len(traces[1]) == len(traces[2])
    traces = list(zip(*traces))
    network = P2PNetwork()

    testCB = {}
    testCB["BOLA"] = (Simple, traces, vi, network, BOLA)
    testCB["FastMPC"] = (Simple, traces, vi, network, AbrFastMPC)
    testCB["RobustMPC"] = (Simple, traces, vi, network, AbrRobustMPC)
    testCB["Penseiv"] = (Simple, traces, vi, network, AbrPensieve)
    testCB["DHTEnvironment"] = (DHT, traces, vi, network)
    testCB["FLiDASH"] = (FLiDASH, traces, vi, network, BOLA, None)

    results = {}
    cdns = {}

#     for name, cb in testCB.items():
    for name in allowed:
        assert name in testCB
        cb = testCB[name]
        randstate.loadCurrentState()
        ags, cdn = runExperiments(*cb)
        results[name] = ags
        cdns[name] = cdn

    print("ploting figures")
    print("="*30)

    lonePeers = findIgnorablePeers(results)

    plotAgentsData(results, "_vAgent.QoE", "QoE", "Player Id", lonePeers)
    plotAgentsData(results, "_vAgent.avgBitrate", "Average bitrate played", "Player Id", lonePeers)
    plotAgentsData(results, "_vAgent.avgQualityIndex", "Average quality index played", "Player Id", lonePeers)
    plotAgentsData(results, "_vAgent.avgQualityIndexVariation", "Average quality index variation", "Player Id", lonePeers)
    plotAgentsData(results, "_vAgent.totalStallTime", "Stall Time", "Player Id", lonePeers)
    plotAgentsData(results, "_vAgent.startUpDelay", "Start up delay", "Player Id", lonePeers)
    plotAgentsData(results, "idleTime", "IdleTime", "Player Id", lonePeers)
    plotAgentsData(results, "_vAgent.avgBitrateVariation", "Average Bitrate Variation", "Player Id", lonePeers)
    plotAgentsData(results, "totalWorkingTime", "workingTime", "Player Id", lonePeers)

    plotCDNData(cdns)

    measureBenefit(results, lonePeers)
#     plt.show()

#     plotBufferLens(results)
#     plotIdleStallTIme(results)



if __name__ == "__main__":
#     for x in range(20):
        main()
#     main2()
