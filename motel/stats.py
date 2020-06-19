"""Statistics and analysis of ensembles and predictions"""

from math import inf, fabs

def statistics(prediction, ground_truth, beta=1):
    """Computes performance statistics for classifiers.

    Parameters
    ----------
    prediction : set
        Set of objects predicted to be labeled positive.

    ground_truth : set
        Set of objects actually labeled positive.

    beta : float, optional
        Sets the beta for an F-beta score. Defaults to 1.

    Returns
    -------
    (float, float, float)
        Tuple representing (precision, recall, f_beta).
    """
    true_positives = ground_truth & prediction
    false_positives = prediction - ground_truth

    if len(prediction) == 0: # to avoid division-by-zero errors
        precision = 0.0
    else:
        precision = len(true_positives) / (len(true_positives) + len(false_positives))
    
    recall = len(true_positives) / len(ground_truth)
    
    if precision == 0.0 and recall == 0.0: # to avoid division-by-zero errors
        f_beta = 0.0
    else:
        f_beta = (1 + beta ** 2) * (precision * recall) / ((beta ** 2 * precision) + recall)
    
    return (precision, recall, f_beta)

def precision_recall_curve(ensemble, ground_truth):
    """Constructs a precision-recall curve for an ensemble.

    Parameters
    ----------
    ensemble : ensembles.Ensemble
        Ensemble with natural classification probabilities per-point.
    
    ground_truth : img.Point set
        Set of points representing the ground-truth positive points.

    Yields
    ------
    dict
        Containing fields "ranking", "point", "precision", "recall", "gt". Yielded in rank-descending order.
    """

    rankings = ensemble.probabilities_per_point().sort(key= lambda p: p[-1], reverse=True)
    selected = set() # to hold the already-selected images

    for (point, ranking) in rankings: # note - we're using the classification probability for the ranking
        selected.add(point)
        try:
            precision, recall, _ = statistics(selected, ground_truth, beta=1)
        except:
            precision, recall = 0, 0
        
        yield {
            "ranking" : ranking,
            "point" : point,
            "precision" : precision,
            "recall" : recall,
            "gt" : point in ground_truth
        }

def min_absolute_logit(ensemble, domain):
    """Returns the point in the domain with the smallest absolute logit.

    The absolute logit value is computed with respect to the ensemble classification probabilities.

    Parameters
    ----------
    ensemble : ensembles.Ensemble
        An ensemble of motifs with a natural classification probability.

    domain : img.Point set
        Set of points to minimize over.

    Returns
    -------
    img.Point or None
        The point in the domain with the smallest absolute logit, or None if one cannot be found.
    """

    point_min, logit_min = None, inf
    for (point, p_true) in ensemble.probabilities_per_point():
        if point in domain:
            abs_logit = fabs(p_true - (1 - p_true)) # the actual logit computation
            if abs_logit <= logit_min:
                point_min, logit_min = point, abs_logit
    return point_min
