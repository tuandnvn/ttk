import json
from ttk_path import TTK_ROOT
from library.timeMLspec import TID, EIID
import math, os
from nltk.corpus import wordnet as wn
import logging
import itertools
from library.classifier.svm_histogram import Histogram as histo
from library.classifier.svm_histogram_posterior import Histogram as histo_post
from library.classifier.classifySpec import KEEP_FEATURES, ET_FLAG_WITH_DCT

logging.basicConfig(filename=os.path.join(TTK_ROOT, 'data', 'logs', 
                                          'incorporate_link_with_prior_correction.log'),
                    level=logging.DEBUG)

"""
This file is a modification of 
tlink_inject_with_prior.py. The name is changed to tlink_relabel,
'cause it doesn't really inject the label, just recalculate the label,
and injecting labels will be transferred to incorporate_tlink_correction.py
It totally disregards the narrative scheme, which proved to be useless.
It also includes all labels from the classifiers, not only [BEFORE, AFTER, *SIMULTANEOUS],
so basically, it includes other labels, such as [INCLUDES, IS_INCLUDED, NORELATION, 
The algorithm is as following:
    
- Calculate P ( result_vector | label ) 
    Get result_vector* corresponding to that label (remove the 
        dimension comparing two other labels).
    Detail of implementation:
    For example:
        Consider:
        result_vector: {"('SIMULTANEOUS', 'AFTER')": 1.0958849, 
                        "('AFTER', 'BEFORE')": -2.1010391, 
                        "('SIMULTANEOUS', 'BEFORE')": -1.7459796}
        result_vector* = {('AFTER', 'BEFORE'): -2.1010391, 
                        ('SIMULTANEOUS', 'BEFORE'): -1.7459796}
        label = BEFORE
        
        P ( result_vector | label ) = P(  -2.1010391 | classifier = ('AFTER', 'BEFORE'), 
                                                        label = BEFORE )
                                    x P(  -1.7459796 | classifier = ('SIMULTANEOUS', 'BEFORE'), 
                                                        label = BEFORE )
                                    
        where P( (Label1, Label2): value | Label1 ) is calculated by histogram bin method
            = 
            Percent of training samples (traing the classifier for Label1
             vs Label2) that fell into the same bin with value
             that has Label1.
        
- The TLINKs is collected, not to inject immediately. 
"""

RESULT_DICT = 'Result_dict'
VOTE_DICT = 'Vote_dict'
TLINK_IDS_DICT = 'Tlink_dict'

def tlink_relabel_with_prior_correction(  result_file, prior ):
    histogram = histo.get_singleton()
    """
    Different from tlink_inject, we don't need no_tlink_file and tlink_file
    'cause the script just recalculate the label for an updated prior.
    Parameters:
        - result_file:
            feature_vector file
        - prior:
            the a prior of the previous distribution 
    """
                
    with open(result_file, 'r') as  result_file:
        label_vote_dict = json.load( result_file )
        
    new_relation_collect = {}
    for feature_type in label_vote_dict:
        new_relation_collect[feature_type] = {}
        """
        feature_type = [main_events_in_consecutive_sentences, etc.]
        """
        for line_counter in label_vote_dict[feature_type]:
            result_dict =  label_vote_dict[feature_type][line_counter][RESULT_DICT]
            label_vote = label_vote_dict[feature_type][line_counter][VOTE_DICT]
            ids = label_vote_dict[feature_type][line_counter][TLINK_IDS_DICT]
            
            raw_relType = label_vote[-1][0]
            """
            Have to re calculate the relType here
            - Calculate P ( label | result_vector ) ~ P(label) 
                                                x P ( result_vector | label )
            """
            
            new_ids = {}
            for id in ids:
                if id[1] in [TID, EIID]:
                    new_ids[id[0]] = id[2]
            
            probability = {}
            max_label = None
            max_prob = None
            
            """
            Only consider labels inside the votes
            """
#             for label in [str(label[0]) for label in result_dict]:
            for label in KEEP_FEATURES[feature_type]:
#                 logging.info('------' + label + '-------')
                probability[label] = 1
                
#                 logging.info('--RESULT PROB--')
                result_prob = histogram.get_probability_vector(result_dict, 
                                                               feature_type, label)
#                 logging.info(result_prob)
                probability[label] *= result_prob
                
                label_prob = prior[feature_type][label]
#                 logging.info('--LABEL PROB--')
#                 logging.info(label_prob)
                probability[label] *= label_prob
            
            """
            Normalization
            """
            sum = 0
            for label in probability:
                sum += probability[label]
            for label in probability:
                if sum != 0:
                    probability[label] /= sum
                else:
                    probability[label] = float(1)/len(probability.keys())
#             for label in probability:
#                 if feature_type == ET_FLAG_WITH_DCT and label == SIMULTANEOUS and probability[label] != 0:
#                     logging.info(result_dict)
#                     logging.info(probability)
            new_relation_collect[feature_type][line_counter] = (probability,
                                                                raw_relType, 
                                                                new_ids['0'],
                                                                new_ids['1'])
    return new_relation_collect

def tlink_relabel_with_prior_correction_posterior(  result_file, prior ):
    histogram = histo_post.get_singleton()
    """
    Different from tlink_inject, we don't need no_tlink_file and tlink_file
    'cause the script just recalculate the label for an updated prior.
    A modification of tlink_relabel_with_prior_correction, instead of
    using histogram, using histogram_posterior. 
    Parameters:
        - result_file:
            feature_vector file
        - prior:
            the a prior of the previous distribution 
    
    """
                
    with open(result_file, 'r') as  result_file:
        label_vote_dict = json.load( result_file )
        
    new_relation_collect = {}
    for feature_type in label_vote_dict:
        new_relation_collect[feature_type] = {}
        """
        feature_type = [main_events_in_consecutive_sentences, etc.]
        """
        for line_counter in label_vote_dict[feature_type]:
            result_dict =  label_vote_dict[feature_type][line_counter][RESULT_DICT]
            label_vote = label_vote_dict[feature_type][line_counter][VOTE_DICT]
            ids = label_vote_dict[feature_type][line_counter][TLINK_IDS_DICT]
            
            raw_relType = label_vote[-1][0]
            """
            Have to re calculate the relType here
            - Calculate P ( label | result_vector ) ~ P(label) 
                                                x P ( result_vector | label )
            """
            
            new_ids = {}
            for id in ids:
                if id[1] in [TID, EIID]:
                    new_ids[id[0]] = id[2]
            
            probability = {}
            
            """
            Only consider labels inside the votes
            """
#             for label in [str(label[0]) for label in result_dict]:
            result_prob = histogram.get_normalized_probability_vector(result_dict, 
                                                               feature_type)
            initial_prior = histogram.get_prior()[feature_type]
            for label in KEEP_FEATURES[feature_type]:
                probability[label] = 1
                probability[label] *= result_prob[label]
                
                label_prob = prior[feature_type][label]
                probability[label] *= label_prob
                
                probability[label] /= initial_prior[label]
            
            """
            Normalization
            """
            sum = 0
            for label in probability:
                sum += probability[label]
            for label in probability:
                if sum != 0:
                    probability[label] /= sum
                else:
                    probability[label] = float(1)/len(probability.keys())
#             for label in probability:
#                 if feature_type == ET_FLAG_WITH_DCT and label == SIMULTANEOUS and probability[label] != 0:
#                     logging.info(result_dict)
#                     logging.info(probability)
            new_relation_collect[feature_type][line_counter] = (probability,
                                                                raw_relType, 
                                                                new_ids['0'],
                                                                new_ids['1'])
    return new_relation_collect
