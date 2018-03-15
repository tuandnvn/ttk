from collections import defaultdict
import json

TAXONOMY = 'Taxonomy'
CALIBRATING_SET = 'Calibrating_multisets'
TAXONOMY_CALIBRATE = 'Taxonomy_calibrate'

class Venn_Predictor:
    """
    Based on the following paper,
    - Reliable probability estimates based on Support Vector Machines
         for large multiclass datasets
      Antonis Lambrou
    - Reliable Probabilistic Classification with Neural Networks
      Harris Papadopoulos
    - Conditional validity of inductive conformal predictors
      Vladimir Vovk
    I design a class for Venn Predictor,
    the idea is based on a trained classifier on silver data
    the calibrating data will be gold data, which will adjust the posteriors
    of test data regarding different classes.
    
    
    """
    def __init__(self, taxonomy):
        """
        Taxonomy should be a list of tuple has the following format
        ( category_name, category_description )
        """
        self._taxonomy = taxonomy
        self._calibrating_multisets = []
        
        self._taxonomy_calibrate = {}
        for category_name, category_description in self._taxonomy:
            self._taxonomy_calibrate[category_name] = defaultdict(float)
        
    def set_taxonomy_classifier(self, classifier):
        """
        Classifier should be a provided function that take in 
        some input and return one of the taxonomy category
        """
        self.taxonomy_classifier = classifier
        
        """
        Reset every elements of multiset here
        """
        self.reset_taxonomy_set()
        
    def reset_taxonomy_set(self):
        self._taxonomy_calibrate = {}
        for sample in self._calibrating_multisets:
            feature_data, sample_true_label = sample
            category_name = self.taxonomy_classifier(sample)
            self._taxonomy_calibrate[category_name][sample_true_label] += 1
        
    def obtain_calibrating_sample (self, sample):
        """
        sample will take the following format:
        ( feature_data, sample_true_label )
        """
        feature_data, sample_true_label = sample
        self._calibrating_multisets.append(sample)
        category_name = self.taxonomy_classifier(sample)
        self._taxonomy_calibrate[category_name][sample_true_label] += 1
    
    def get_posterior( self, test_sample ):
        """
        Given a test sample, the posterior of the test_sample will
        depend on the label distribution of calibrating data 
        that shares the same category as the test_sample
        """
        test_category_name = self.taxonomy_classifier(test_sample)
        calib_count = self._taxonomy_calibrate[test_category_name]
        for label in calib_count:
            calib_count[label] += float(1)/len(calib_count.keys())
        calib_prob = get_prob(calib_count)
        return calib_prob
        
    
    @staticmethod
    def get_prob ( count_array ):
        sum = sum(count_array)
        for i in xrange(len(count_array)):
            count_array[i] = double(count_array[i])/sum
        return count_array
    
    def save(self, filename):
        with open(filename, 'w') as f:
            json.dump({TAXONOMY: self._taxonomy, 
                       CALIBRATING_SET: self._calibrating_multisets,
                       TAXONOMY_CALIBRATE: self._taxonomy_calibrate}, 
                      filename)
    
    def load(self, filename):
        with open(filename, 'r') as f:
            o = json.read(filename)
            self._taxonomy = o[TAXONOMY]
            self._calibrating_multisets = o[CALIBRATING_SET]
            self._taxonomy_calibrate = o[TAXONOMY_CALIBRATE]
    