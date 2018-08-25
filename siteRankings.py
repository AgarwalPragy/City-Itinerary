__all__ = ['alexa_ranking', 'similar_web_ranking', 'alexa_ranking_orderedList']

alexa_score = {
    'tripexpert' : 100,
    'tripAdvisor': 204,
    'skyscanner': 2997,
    'viator_v2':  3918,
    'inspirock': 12066
}


similar_web_score = {
    'tripexpert' : {'gRank': 100,   'catRank': 1},
    'tripAdvisor': {'gRank':   140, 'catRank':   1},
    'skyscanner':  {'gRank':  3948, 'catRank':  23},
    'viator_v2':   {'gRank':  5152, 'catRank':  39},
    'inspirock':   {'gRank': 20298, 'catRank': 212}
}


alexa_ranking = {
    'tripexpert' : 1,
    'tripAdvisor': 2,
    'skyscanner':  30,
    'viator_v2':   40,
    'inspirock':   120
}

alexa_ranking_orderedList = ['tripexpert', 'tripAdvisor', 'skyscanner', 'viator_v2', 'inspirock']

similar_web_ranking = {
    'tripexpert' : 1,
    'tripAdvisor': 2,
    'skyscanner':  39,
    'viator_v2':   51,
    'inspirock':   200
}