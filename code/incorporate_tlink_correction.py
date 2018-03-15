from ttk_path import TTK_ROOT
from utilities.tlink_change import tlink_inject, tlink_remove
from utilities.tlink_relabel_with_prior_correction import\
                 tlink_relabel_with_prior_correction as trwpc,\
                 tlink_relabel_with_prior_correction_posterior as trwpcp

import glob
import os
import logging
from docmodel.xml_parser import Parser
from library.dataSpec import *
from library.classifier.classifySpec import EE_FLAG_MAIN_INTRA_SENT, EE_FLAG_MAIN_INTER_SENT,\
                                ET_FLAG_CONSE_SENT, ET_FLAG_WITH_DCT
from library.classifier.svm_histogram import Histogram as histo
from library.classifier.svm_histogram_posterior import Histogram as histo_post
from library.tlink_relation import NORELATION
from collections import defaultdict

logging.basicConfig(filename=os.path.join(TTK_ROOT, 'data', 'logs', 
                                          'incorporate_link_with_prior_correction.log'),
                    level=logging.DEBUG)


"""
This file is a modification of incorporate_tlink
with the incorporate of the idea given from this paper:

ftp://iridia.ulb.ac.be/pub/latinne/MARCH/apriori.pdf

The idea is like this:
Currently, when calculating the a posterior to classify
using bin method, I use the calculated a prior learnt from
the silver data (it's not exactly the a prior of the whole data
but the a prior corresponding to the imposed ML model). However, 
that a prior doesn't reflect the correct a prior in the testing data,
therefore we could use EM to correct that prior, until the 
result converge, and we end up using the resulted labels, rather
than the original labels.

Corresponding to this script, I included an additional injection script:
utilites.tlink_inject_with_prior_correction.py
"""
SVM_CLASSIFIER_ORIGIN = 'TreeSvm Classifier'

SILVER_SVM_HISTOGRAM_POSTERIOR_FILE = os.path.join( TTK_ROOT, 'library', 'classifier',
                                    'svm_histogram', 'silver_reclassify_statistic_posterior.stat')
GOLD_SVM_HISTOGRAM_POSTERIOR_FILE = os.path.join( TTK_ROOT, 'library', 'classifier',
                                    'svm_histogram', 'gold_reclassify_statistic_posterior.stat')
SILVER_SVM_HISTOGRAM_POSTERIOR_FILE_NEW_LABELS = os.path.join( TTK_ROOT, 'library', 'classifier',
                                    'svm_histogram', 'silver_reclassify_statistic_posterior_new_labels.stat')


GOLD_SVM_HISTOGRAM_POSTERIOR_FILE_2 = os.path.join( TTK_ROOT, 'library', 'classifier',
                                    'svm_histogram', 'gold_reclassify_statistic_posterior_2.stat')

SILVER_SVM_HISTOGRAM_FILE = os.path.join( TTK_ROOT, 'library', 'classifier',
                                    'svm_histogram', 'silver_reclassify_statistic.stat')
GOLD_SVM_HISTOGRAM_FILE = os.path.join( TTK_ROOT, 'library', 'classifier',
                                    'svm_histogram', 'gold_reclassify_statistic.stat')
SILVER_SVM_HISTOGRAM_FILE_NEW_LABELS = os.path.join( TTK_ROOT, 'library', 'classifier',
                                    'svm_histogram', 'silver_reclassify_statistic_new_labels.stat')

# histogram.load_histogram(SVM_HISTOGRAM_FILE)

def incorporate_tlink_with_prior_correction( svm_histogram_file,
                                             no_tlink_directory, 
                                             result_directory, 
                                             tlink_directory, 
                                             histogram_class,
                                             correction_method):
    
    histogram = histogram_class.load_histogram(svm_histogram_file)
    result_files = glob.glob(os.path.join(result_directory, 
                                            '*%s' % RESULT_SUFFIX))
    total_fix_label_counter = 0
    total_worsen_label_counter = 0
    
    prior = histogram.get_prior()
    
    """
    Should be converging condition
    """
    all_relation_collect = {}
    for i in xrange(2):
        print i
        logging.info('======================RUN========================')
        logging.info(i)
        for feature_type in  prior:
            logging.info(feature_type)
            logging.info( prior[feature_type] )
            
        label_prob_collect = {}
        for result_file in result_files:
            new_relation_collect = correction_method(result_file, prior)
            for feature_type in new_relation_collect:
                if feature_type not in label_prob_collect:
                    label_prob_collect[feature_type] = {}
                label_prob_collect[feature_type][result_file] = new_relation_collect[feature_type]
        
        all_relation_collect[i] = label_prob_collect
        
        new_prior = {}
        new_prior_count = defaultdict(int)
        
        """
        update prior here
        Update prior based on the posterior received 
        from classifying each sample on test data.
        """
        for feature_type in label_prob_collect:
            new_prior[feature_type] = defaultdict(float)
            for result_file in label_prob_collect[feature_type]:
                for line_counter in label_prob_collect[feature_type][result_file]:
                    probability, raw_relType, id_0, id_1 =\
                     label_prob_collect[feature_type][result_file][line_counter]
                    new_prior_count[feature_type] += 1
                    
                    max_value = max(probability.values())
#                     
                    tf = sorted(probability.values())
                    if tf[0] == tf[1]:
                        print probability
                    for label in probability:
                        new_prior[feature_type][label] += probability[label]
            for label in new_prior[feature_type]:
                new_prior[feature_type][label] /=  new_prior_count[feature_type]
        """
        Second way of update prior:
        Update prior on the real label assigned to each
        sample each iteration. 
        It's the extremity version of first prior approach,
        by actually assign for each label a posterior of 1 
        for the most likely label.
        """
#         for feature_type in label_prob_collect:
#             new_prior[feature_type] = defaultdict(float)
#             for result_file in label_prob_collect[feature_type]:
#                 for line_counter in label_prob_collect[feature_type][result_file]:
#                     probability, raw_relType, id_0, id_1 =\
#                      label_prob_collect[feature_type][result_file][line_counter]
#                     new_prior_count[feature_type] += 1
#                     max_value = max(probability.values())
#                     
#                     tf = sorted(probability.values())
#                     if tf[0] == tf[-1]:
#                         new_prior[feature_type][raw_relType] += 1
#                     else:    
#                         for label in probability:
#                             if probability[label] == max_value:
#                                 new_prior[feature_type][label] += 1
#                                 break
#             for label in new_prior[feature_type]:
#                 new_prior[feature_type][label] /=  new_prior_count[feature_type]
        
        prior = new_prior
        
    """
    Check this part first
    """
#     return
    result_file_collect = {}
    for feature_type in label_prob_collect:
        if feature_type in [
                            ]:
            for result_file in all_relation_collect[0][feature_type]:
                if result_file not in result_file_collect:
                    result_file_collect[result_file] = {}
                result_file_collect[result_file][feature_type] =\
                    all_relation_collect[0][feature_type][result_file]
        else:    
            for result_file in label_prob_collect[feature_type]:
                if result_file not in result_file_collect:
                    result_file_collect[result_file] = {}
                result_file_collect[result_file][feature_type] =\
                    label_prob_collect[feature_type][result_file]
    for result_file in result_file_collect:
        rel_filename = result_file[result_file.rindex(os.path.sep) + 1:]
        no_tlink_file = os.path.join(no_tlink_directory,
                                       '%s%s' % (rel_filename[:-len(RESULT_SUFFIX)],
                                    NO_TLINK_SUFFIX) )
        tlink_file = os.path.join(tlink_directory,
                                  '%s%s' % (rel_filename[:-len(RESULT_SUFFIX)],
                                    ADD_TLINK_SUFFIX) )
        
        xml_document = Parser().parse_file(open(no_tlink_file, "r"))    
        for feature_type in result_file_collect[result_file]:
            for line_counter in result_file_collect[result_file][feature_type]:
                (probability, raw_relType, id_0, id_1) =\
                     result_file_collect[result_file][feature_type][line_counter]
                tf = sorted(probability.values())
                if tf[0] == tf[-1]:
                    """
                    I should fix the label here to the label
                    guessed by vote dict
                    """
                    relType = raw_relType
                else:
                    if tf[-1] == tf[-2]:
                        print probability
                    relType = sorted(probability.items(), key = lambda x:x[1])[-1][0]
                if relType != NORELATION:
                    xml_document.add_tlink(relType, id_0,
                                        id_1, SVM_CLASSIFIER_ORIGIN)
        xml_document.save_to_file (tlink_file)

"""
{"main_events_in_consecutive_sentences": {"1": {"Result_dict": {"('SIMULTANEOUS', 'AFTER')":
 1.0958849, "('AFTER', 'BEFORE')": -2.1010391, "('SIMULTANEOUS', 'BEFORE')":
"""
RESULT_DIRECTORY_NEW_FORMAT = os.path.join(TTK_ROOT, 'data', 'raw_result_new_format')

"""
When we use narrative scheme as priors
"""
ADDED_TLINK_DIRECTORY_WITH_PRIOR_CORRECTION = os.path.join(TTK_ROOT, 
                                                           'data', 
                                                           'added_tlink_with_prior_correction')

# incorporate_tlink_with_prior_correction( GOLD_SVM_HISTOGRAM_FILE,
#                                          TEST_NO_TLINK_DIRECTORY, 
#                                          RESULT_DIRECTORY_NEW_FORMAT, 
#                                          ADDED_TLINK_DIRECTORY_WITH_PRIOR_CORRECTION,
#                                          histo,
#                                          trwpc)


# incorporate_tlink_with_prior_correction( GOLD_SVM_HISTOGRAM_POSTERIOR_FILE,
#                                          TEST_NO_TLINK_DIRECTORY, 
#                                          RESULT_DIRECTORY_NEW_FORMAT, 
#                                          ADDED_TLINK_DIRECTORY_WITH_PRIOR_CORRECTION,
#                                          histo_post,
#                                          trwpcp)

# incorporate_tlink_with_prior_correction( SILVER_SVM_HISTOGRAM_FILE,
#                                          TEST_NO_TLINK_DIRECTORY, 
#                                          RESULT_DIRECTORY_NEW_FORMAT, 
#                                          ADDED_TLINK_DIRECTORY_WITH_PRIOR_CORRECTION,
#                                          histo,
#                                          trwpc)

# incorporate_tlink_with_prior_correction( SILVER_SVM_HISTOGRAM_FILE_NEW_LABELS,
#                                          TEST_NO_TLINK_DIRECTORY, 
#                                          RESULT_DIRECTORY_NEW_FORMAT, 
#                                          ADDED_TLINK_DIRECTORY_WITH_PRIOR_CORRECTION,
#                                          histo,
#                                          trwpc)

incorporate_tlink_with_prior_correction( SILVER_SVM_HISTOGRAM_POSTERIOR_FILE,
                                         TEST_NO_TLINK_DIRECTORY, 
                                         RESULT_DIRECTORY_NEW_FORMAT, 
                                         ADDED_TLINK_DIRECTORY_WITH_PRIOR_CORRECTION,
                                         histo_post,
                                         trwpcp)

# incorporate_tlink_with_prior_correction( SILVER_SVM_HISTOGRAM_POSTERIOR_FILE_NEW_LABELS,
#                                          TEST_NO_TLINK_DIRECTORY, 
#                                          RESULT_DIRECTORY_NEW_FORMAT, 
#                                          ADDED_TLINK_DIRECTORY_WITH_PRIOR_CORRECTION,
#                                          histo_post,
#                                          trwpcp)