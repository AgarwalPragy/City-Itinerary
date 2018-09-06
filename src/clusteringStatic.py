from functools import lru_cache
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt

from equal_groups import EqualGroupsKMeans
from utilities import latlngDistance
import time


def allPossibleOrders(centers, sequence, lastCenter, distance, allSequenes):
    for index, center in enumerate(centers):
        newSequence = sequence[:]
        newSequence.append(center)
        newCenters = centers[:]
        newCenters.remove(center)

        newDistance = 0
        if lastCenter:
            newDistance = distance + latlngDistance(*lastCenter, *center)

        if newCenters:
            allPossibleOrders(newCenters, newSequence, center, newDistance, allSequenes)
        else:
            seqData = {'sequence': newSequence, 'distance': newDistance}
            allSequenes.append(seqData)


def getBestOrder(centers):
    sequence = []
    allOrders = []

    allPossibleOrders(centers, sequence, None, 0, allOrders)

    print('possible sequence generated: ', len(allOrders))
    minDistance = float('inf')
    bestOrder = None

    for order in allOrders:
        if minDistance > order['distance']:
            minDistance = order['distance']
            bestOrder = order

    bestOrder = bestOrder['sequence']
    return bestOrder


@lru_cache(None)
def cluster(X, numClusters, debug=False):
    t1 = time.time()
    X = np.array(X)
    clustering = EqualGroupsKMeans(n_clusters=numClusters, init='k-means++', n_init=2, max_iter=100, tol=1e-6).fit(X)
    centers = clustering.cluster_centers_.tolist()
    bestOrder = getBestOrder(centers)

    labelMap = {label: bestOrder.index(center) for label, center in enumerate(centers)}
    t2 = time.time()
    print('Clustering took {} seconds'.format(t2-t1))
    if debug:
        t1 = time.time()
        plt.scatter(X[:,0], X[:,1], c=clustering.labels_, cmap='rainbow')
        plt.savefig('clustering.jpg')
        plt.close()
        t2 = time.time()
        print('Plotting took {} seconds'.format(t2-t1))
    return clustering.labels_, labelMap




if __name__ == '__main__':
    np.random.seed(0)
    X = np.random.random((64, 2))
    cluster(X, 8, debug=True)

