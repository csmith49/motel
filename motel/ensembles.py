"""Ensembles of motifs"""

import numpy as np
import settings, log

logger = log.get("ensembles")

class Ensemble:
    """Ensemble base class.
    
    Parameters
    ----------
    image : img.SparseImage
        A sparse image encoding a set of motifs and the points they select from a data set.

    Attributes
    ----------
    size : int
        Number of motifs present in the ensemble.

    domain : img.Point list
        Points classified by motifs in the ensemble.

    motifs : motifs.Motif list
        Motifs present in the ensemble.
    """

    def __init__(self, image):
        # keep the image around for a few things
        logger.info(f"Building ensemble from image {image}...")
        self._image = image
        self._point_map = list(image.domain)
        self._motif_map = image.motifs
        # construct inclusion matrix by building rows per-motif
        rows = []
        for motif in self._motif_map:
            rows.append(self._to_row(image.motif_domain(motif)))
        self._inclusion = np.transpose(np.array(rows))
        logger.info(f"Ensemble {self} built with {len(self._motif_map)} motifs and {len(self._point_map)} points.")

    def _to_row(self, points):
        """Converts a list of points to a row in the ensemble's inclusion matrix.

        Parameters
        ----------
        points : img.Point list
            A list of points classified by a single motif

        Returns
        -------
        np.Array
            A 0-1 integer array representing the provided list of points

        Notes
        -----
        Internal helper function, not intended for use outside this base class.

        Functional inverse of `_to_points`.
        """
        row = [1 if point in points else 0 for point in self._point_map]
        return np.array(row)

    def _to_points(self, row):
        """Converts a row in the ensemble's inclusion matrix to a list of points.

        Parameters
        ----------
        row : np.Array
            A 0-1 np.Array from a row in the inclusion matrix.

        Returns
        -------
        img.Point list
            List of points encoded in the provided row.

        Notes
        -----
        Internal helper function, not intended for use outside this base class.

        Functional inverse of `_to_row`.
        """
        result = []
        for point, value in zip(self._point_map, np.nditer(row, order='C')):
            if value:
                result.append(point)
        return result

    @property
    def size(self):
        return len(self._motif_map)
    
    @property
    def domain(self):
        return self._point_map

    @property
    def motifs(self):
        return self._motif_map

    def motif_domain(self, motif):
        """Set of points classified by a motif in the ensemble.

        Parameters
        ----------
        motif : motifs.Motif
            A motif object in the ensemble.

        Returns
        -------
        img.Point list
            A list of points classified by the provided motif.
        
        See Also
        --------
        `domain` - the `domain` attribute gives the list of points classified by all motifs in the ensemble.
        """
        return self._image.motif_domain(motif)

    def classify(self, point):
        """Classifies a single point using the ensemble.

        Parameters
        ----------
        point : img.Point
            A point-to-be-classified.

        Returns
        -------
        bool
            True/false classification of the provided point.

        Notes
        -----
        Assumes the class extending `Ensemble` uses `classified` to determine what is and isn't classified.
        """
        return (point in self.classified())

    def update(self):
        """Updates some internal state to "improve" the ensemble. Intended to be overwritten.

        Raises
        ------
        NotImplementedError
        """
        raise NotImplementedError

    def classified(self, threshold=None):
        """Provides a set of positively-classified points.

        Parameters
        ----------
        threshold : float, optional
            A [0,1]-valued threshold indicating the minimum positive probability for a point to be classified. Defaults to `settings.CLASSIFICATION_THRESHOLD`.

        Returns
        -------
        img.Point list
            List of points in the ensemble domain with sufficiently high classification probability.

        Notes
        -----
        Assumes the class extending `Ensemble` uses `probabilities` to determine confidence of classification.
        """
        if threshold is None:
            threshold = settings.CLASSIFICATION_THRESHOLD
        return self._to_points(self.probabilities() >= threshold)

    def probabilities(self):
        """Provides classification probabilities for points in the ensemble's domain. Intended to be overwritten.

        Returns
        -------
        np.Array
            An [0,1]-valued np.Array whose dimensions match the `Ensemble._point_map` attribute.

        Raises
        ------
        NotImplementedError
        """
        raise NotImplementedError

    def probabilities_per_point(self):
        """Provide classification probabilities for every point in the domain as a list of pairs.

        Returns
        -------
        (img.Point, float) list
            A list of points in the ensemble domain paired-up with their positive classification probabilities.
        """
        return zip(self._point_map, self.probabilities())

class Disjunction(Ensemble):
    """Ensemble computing classification via a "disjunction" of individual motif classifications.

    Parameters
    ----------
    image : img.SparseImage
        A sparse image encoding a set of motifs and the points they select from a data set.
    
    accuracy_smoothing : int, optional
        Constant integer to add to numerators and denominators to smooth accuracy computations. Defaults to 1.
    
    Attributes
    ----------
    size : int
        Number of *relevant* motifs present in the ensemble.

    domain : img.Point list
        Points classified by motifs in the ensemble.

    motifs : motifs.Motif list
        Motifs present in the ensemble.

    accuracies : np.Array
        1-dimensional float array encoding accuracies per-motif. Indices match that of the `motifs` attribute.
    """
    def __init__(self, image, accuracy_smoothing=1):
        # build inclusion matrix, via super
        super().__init__(image)
        # keep observations for accuracy computations
        self._observations = []
        # and a set of accuracies built from observations
        self._accuracy_smoothing = accuracy_smoothing
        self.accuracies = np.ones(len(self._motif_map))

    def update(self, point, classification):
        """Update the per-motif accuracy prediction, given an observation.

        Parameters
        ----------
        point : img.Point
            A point in the ensemble's domain whose classification has been observed.

        classification : bool
            The classification of the observed point.
        """
        self._observations.append( (point, classification) )
        accuracies = []
        for motif in self._motif_map:
            prediction = point in self.motif_domain(motif)
            correct = sum([1 for (point, classification) in self._observations if prediction == classification])
            total = len(self._observations)
            accuracies.append(
                (correct + self._accuracy_smoothing) / (total + self._accuracy_smoothing)
            )
        self.accuracies = np.array(accuracies)

    def _relevant_motifs(self):
        """Select all motifs with accuracy above a particular threshold.

        Returns
        -------
        np.Array
            A 0-1 array indicating which motifs have accuracies above a threshold.

        Notes
        -----
        The accuracy threshold is determined by the value `settings.ACCURACY_THRESHOLD`.
        """
        return np.where(
            self.accuracies >= settings.ACCURACY_THRESHOLD,
            np.ones_like(self.accuracies),
            np.zeros_like(self.accuracies)
        )

    def probabilities(self):
        """Probability of positive classification per point in the domain.

        In a disjunction ensemble, probabilities are 0 if *no* motif selects the point, and 1 otherwise.

        Returns
        -------
        np.Array
            An 0-or-1 np.Array whose dimensions match the `Ensemble._point_map` attribute.

        """
        counts = self._inclusion @ np.transpose(self._relevant_motifs())
        return np.where(
            counts > 0,
            np.ones_like(counts),
            np.zeros_like(counts)
        )

    @property
    def size(self):
        # overriding, as we would like to only use "relevant" motifs
        return np.sum(self._relevant_motifs())

class MajorityVote(Disjunction):
    """Ensembles computing classifications by taking a majority vote over motifs in the ensemble.

    Parameters
    ----------
    image : img.SparseImage
        A sparse image encoding a set of motifs and the points they select from a data set.
    
    accuracy_smoothing : int, optional
        Constant integer to add to numerators and denominators to smooth accuracy computations. Defaults to 1.
    
    Attributes
    ----------
    size : int
        Number of motifs present in the ensemble.

    domain : img.Point list
        Points classified by motifs in the ensemble.

    motifs : motifs.Motif list
        Motifs present in the ensemble.

    accuracies : np.Array
        1-dimensional float array encoding accuracies per-motif. Indices match that of the `motifs` attribute.
    """

    def probabilities(self):
        """Probabilities of positive classification per point in the ensemble's domain.

        In a majority vote, the probability is proportional to the number of motifs selecting the relevant point.

        Returns
        -------
        np.array
            An [0,1]-valued np.Array whose dimensions match the `Ensemble._point_map` attribute.
        """
        relevant = self._relevant_motifs()
        counts_for = self._inclusion @ np.transpose(relevant)
        return counts_for / self.size


class WeightedVote(Ensemble):
    """Ensemble using a weighted vote over motifs to classify points.
    
    Parameters
    ----------
    image : img.SparseImage
        A sparse image encoding a set of motifs and the points they select from a data set.

    approximate_fpr : bool, optional
        If `True`, false-positive rate is approximated using per-motif accuracy estimates. Otherwise, FPR is uniform. Defaults to `True`.

    Attributes
    ----------
    size : int
        Number of motifs present in the ensemble.

    domain : img.Point list
        Points classified by motifs in the ensemble.

    motifs : motifs.Motif list
        Motifs present in the ensemble.
    """
    def __init__(self, image, approximate_fpr=True):
        super().__init__(image)
        accuracy = np.array([len(image.motif_domain(motif)) for motif in self._motif_map]) / self.size
        # initialize false-positive rate
        if approximate_fpr:
            self._fpr = (accuracy - 1) / 2
        else:
            self._fpr = np.ones(len(self._motif_map)) * 0.1
        # internal weight matrix
        self._w_c = accuracy

    def update(self, point, classification, learning_rate=None, decay=1, step=0, scale=1):
        """Update per-motif weights, given an observation.

        Parameters
        ----------
        point : img.Point
            The point being observed.
        
        classification : bool
            The classification of the observation.

        learning_rate : float, optional
            Value scaling the amount internal weights are updated by. Defaults to `settings.LEARNING_RATE`.

        decay : float, optional
            Value determining by how much subsequent updates are scaled by. Defaults to 1.0.

        step : int, optional
            How many updates we've done so far - used to scale subsequent updates. Defaults to 0, making `decay` a non-factor.

        scale : float, optional
            Amount to scale positive observations by. Defaults to 1.0.
        """
        # pull learning rate
        if learning_rate is None:
            learning_rate = settings.LEARNING_RATE
        # multiplicative updates to alpha
        v_i = self._point_map.index(point)
        if classification:
            m_i = self._inclusion[v_i,] * -1 * scale
        else:
            m_i = self._inclusion[v_i,]

        self._fpr *= np.exp(-1 * learning_rate * m_i * (decay ** step))

    def probabilities(self):
        """Probabilities of positive classification for each point in the ensemble's domain.

        In a weighted vote, the probability is proportional to the sum of the weights per motif selecting the point.

        Returns
        -------
        np.array
            An [0,1]-valued np.Array whose dimensions match the `Ensemble._point_map` attribute.
        """
        w_i = self._w_c - 2 * self._fpr

        s_plus = self._inclusion @ np.transpose(w_i)
        s_minus = (1 - self._inclusion) @ np.transpose(w_i)
        denom = max(np.max(s_plus), np.max(s_minus))

        plus = np.exp(s_plus / denom)
        minus = np.exp(s_minus / denom)

        return plus / plus + minus