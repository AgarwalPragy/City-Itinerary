from utilities import latlngDistance
import time

def allPossibleOrders(centers, sequence, lastCenter, distance, allSequenes):
    for center in centers:
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




centers = [[2, 3]]#, [1, 2], [4, 5], [0, 3], [4, 5], [6, 7], [3, 5], [5, 6]]

bestOrder = getBestOrder(centers)
print(bestOrder)
