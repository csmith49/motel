"""Statistics and analysis of ensembles and predictions"""

import log, ensembles, doc
from math import inf, fabs

logger = log.get("stats")

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

# output row construction and header
result_header = [
    "ensemble",
    "precision",
    "recall",
    "f-beta",
    "al-step",
    "threshold"
]

def result_row(predicted, ground_truth, ensemble=None, step=0, threshold=0):
    precision, recall, f_beta = statistics(predicted, ground_truth)
    return {
        "ensemble" : ensemble,
        "al-step" : step,
        "precision" : precision,
        "recall" : recall,
        "f_beta" : f_beta,
        "threshold" : threshold
    }

def evaluate_disjunction(image, dataset):
    # build ensemble and get ground truth
    logger.info(f"Constructing disjunctive enseble from {image}...")
    ensemble = ensembles.Disjunction(image)
    logger.info(f"Extracting ground truth from {dataset}...")
    ground_truth = set(dataset.ground_truth(split=doc.Split.TEST))
    # evaluate
    logger.info(f"Evaluating ensemble {ensemble}...")
    predicted = set(dataset.filter_points(ensemble.classified(), doc.Split.TEST))
    stats = result_row(predicted, ground_truth, ensemble="disjunction")
    logger.info(f"Ensemble {ensemble} evaluated.")
    logger.info(f"Ensemble {ensemble} performance (P / R): {stats['precision']} / {stats['recall']}")
    return [stats]

def evaluate_majority_vote(image, dataset, thresholds=10):
    # load the data
    logger.info(f"Constructing majority vote ensemble from {image}...")
    ensemble = ensembles.MajorityVote(image)
    logger.info(f"Extracting ground truth from {dataset}...")
    ground_truth = set(dataset.ground_truth(split=doc.Split.TEST))
    # start evaluation
    results = []
    logger.info(f"Evaluating ensemble {ensemble}...")
    for threshold in [i / thresholds for i in range(0, thresholds)]:
        # compute stats
        logger.info(f"Evaluating ensemble {ensemble} with threshold {threshold}...")
        predicted = set(dataset.filter_points(ensemble.classified(threshold=threshold), doc.Split.TEST))
        stats = result_row(predicted, ground_truth, ensemble="weighted-majority", threshold=threshold)
        logger.info(f"Ensemble {ensemble} with threshold {threshold} evaluated.")
        logger.info(f"Ensemble {ensemble} performance (P / R): {stats['precision']} / {stats['recall']}")
        results.append(stats)
    return results

def evaluate_weighted_vote(image, dataset, active_learning_steps=10):
    # load the data
    logger.info(f"Constructing weighted vote ensemble from {image}...")
    ensemble = ensembles.WeightedVote(image)
    logger.info(f"Extracting ground truth from {dataset}...")
    ground_truth = set(dataset.ground_truth(split=doc.Split.TEST))
    # build active learning data
    learnable = set(dataset.filter_points(image.domain, split=doc.Split.TEST))
    learned = set()
    # start evaluation
    results = []
    logger.info(f"Evaluating ensemble {ensemble}...")
    for step in range(active_learning_steps):
        # compute stats
        logger.info(f"Evaluating ensemble {ensemble} on active-learning step {step}...")
        predicted = set(dataset.filter_points(ensemble.classified(), doc.Split.TEST))
        stats = result_row(predicted, ground_truth, ensemble="weighted-majority", threshold=threshold)
        logger.info(f"Ensemble {ensemble} on active-learning step {step} evaluated.")
        logger.info(f"Ensemble {ensemble} performance (P / R): {stats['precision']} / {stats['recall']}")
        results.append(stats)
        # see if we can split
        if step != (active_learning_steps - 1):
            logger.info(f"Looking for a split for ensemble {ensemble}...")
            split = min_absolute_logit(ensemble, learnable - learned)
            if split is not None:
                learnable.remove(split)
                learned.add(split)
                truth = (split in ground_truth)
                logger.info(f"Split {split} found with ground truth {truth}.")
                # update the ensemble
                logger.info(f"Updating ensemble {ensemble}...")
                ensemble.update(split, truth, learning_rate=None, decay=1, step=step, scale=1)
                logger.info(f"Ensemble {ensemble} updated.")
            else:
                logger.info(f"No viable split found for ensemble {ensemble}.")
    return results