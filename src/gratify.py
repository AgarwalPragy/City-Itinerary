from tunable import pointAttributeWeights, orderWeightOfPolicies, pointGratificationBasedOn, mScoreAvgRatingCount, mScoreAvgRating
from tunable import goodWordWeight, badWordWeight, okayWordWeight, titleWeight, categoryWeight, pointAvgRank
from tunable import okayCategoryTitleWords, goodCategoryTitleWords, badCategoryTitleWords, thresholdGoodWordCount, freqWithDomainRankingScaleFactor
from tunable import avgTripExpertScore
from utilities import getWilsonScore, processName
from entities import PointAggregated


def getCategoryTitleWeight(point: PointAggregated):
    title = processName(point.pointName)
    categories = processName((point.category if point.category else ''))
    score = None
    goodWordCount = ( sum(titleWeight for word in goodCategoryTitleWords if processName(word) in title)
                    + sum(categoryWeight for word in goodCategoryTitleWords if processName(word) in categories))
    badWordCount  = ( sum(titleWeight for word in badCategoryTitleWords if processName(word) in title)
                    + sum(categoryWeight for word in badCategoryTitleWords if processName(word) in categories))
    okayWordCount = ( sum(titleWeight for word in okayCategoryTitleWords if processName(word) in title)
                    + sum(categoryWeight for word in okayCategoryTitleWords if processName(word) in categories))

    if goodWordCount >= thresholdGoodWordCount:
        score = goodWordWeight * (goodWordCount ** 0.5) + okayWordWeight * (okayWordCount ** 0.5)
    else:
        score = goodWordWeight * (goodWordCount ** 0.5) + badWordWeight * (badWordCount ** 0.5) + okayWordWeight * (okayWordCount ** 0.5)
    return score


def pointFrequency(point: PointAggregated):
    return len(point.sources_crawlers)


def wilsonScoreLB(point):
    return getWilsonScore(point.avgRating/10, point.ratingCount)


def _old_freqWithWeightedDomainRanking(point):
    # rank = (-point.rank) if point.rank else -float('inf')  # lower rank is better
    # return len(point.sources_crawlers), rank                        # first sort on len, then on rank
    rank = -point.rank if point.rank else -pointAvgRank
    return freqWithDomainRankingScaleFactor * len(point.sources_crawlers) + rank


def weightAvgRating(point):
    return point.avgRating


def mayurScore(point):
    avgRating = point.avgRating
    ratingCount = point.ratingCount
    return (avgRating * ratingCount + mScoreAvgRating * mScoreAvgRatingCount) / (ratingCount + mScoreAvgRatingCount)  # inject fake ratings


def getWeightedOrderValueOverDiffPolices(point: PointAggregated):
    result = 0
    jsonPointAggregated = point.jsonify()
    if 'frequency' in orderWeightOfPolicies:
        result += len(jsonPointAggregated['sources_crawlers']) * orderWeightOfPolicies['frequency']

    if 'rank' in orderWeightOfPolicies and jsonPointAggregated['rank'] is not None:
        result -= jsonPointAggregated['rank'] * orderWeightOfPolicies['rank']

    if 'wilsonScore' in orderWeightOfPolicies:
        result += getWilsonScore(jsonPointAggregated['avgRating']/10, jsonPointAggregated['ratingCount']) * orderWeightOfPolicies['wilsonScore']

    if 'pointAttributes' in orderWeightOfPolicies:
        pointAttrValue = 0
        for pointAttr in pointAttributeWeights:
            if jsonPointAggregated[pointAttr] is not None:
                pointAttrValue += pointAttributeWeights[pointAttr]

        result += pointAttrValue * orderWeightOfPolicies['pointAttributes']

    if 'tripexpertScore' in orderWeightOfPolicies:
        tripScore = None
        if jsonPointAggregated['tripexpertScore'] is not None:
            tripScore = jsonPointAggregated['tripexpertScore']
        else:
            tripScore = avgTripExpertScore
        result += tripScore * orderWeightOfPolicies['tripexpertScore']


    if 'category' in orderWeightOfPolicies:
        result += getCategoryTitleWeight(point) * orderWeightOfPolicies['category']

    if 'mayurScore' in orderWeightOfPolicies:
        result += mayurScore(point) * orderWeightOfPolicies['mayurScore']

    if 'frequencyWithWDomainRanking' in orderWeightOfPolicies:
        result += _old_freqWithWeightedDomainRanking(point) * orderWeightOfPolicies['frequencyWithWDomainRanking']

    return result


def gratificationScoreOfPoint(point: PointAggregated):
    keyFunction = {
        'frequency': pointFrequency,
        'wilsonScore': wilsonScoreLB,
        'weightedAvgRating': weightAvgRating,
        'frequencyWithWDomainRanking': _old_freqWithWeightedDomainRanking,
        'mayurScore': mayurScore,
        'weightedOverDiffPolicies': getWeightedOrderValueOverDiffPolices
    }

    return keyFunction[pointGratificationBasedOn](point)
