from collections import defaultdict
import glob
import json
import math
import os
import re
from numpy.core.fromnumeric import sum


RECLASSIFY_SUFFIX = '.reclassifiy' 
BIN_STEP = 'bin_step'
TOTAL_HISTOGRAM = 'total_histogram'
PRIOR = 'prior'

class Histogram:
    def __init__(self, bin_step = None):
        self.total_histogram = {}
        self.bin_step = bin_step
    
    @classmethod
    def get_singleton(cls):
        return cls.instance
        
        
    def get_histogram( self , statistic_file ):
        """
        [["SIMULTANEOUS", "AFTER"], "AFTER", 2.6686243]
        """
        histogram_bin = {}
        label_count = {}
        with open(statistic_file, 'r') as  statistic_file:
            statistic_list = json.load( statistic_file )
            for feature_type in statistic_list:
                if feature_type not in histogram_bin:
                    histogram_bin[feature_type] = {}
                if feature_type not in label_count:
                    label_count[feature_type] = defaultdict(int)
                
                for result_instance in statistic_list[feature_type]:
                    original_label = None
                    for versus_labels, label, svm_value in result_instance:
                        if original_label == None:
                            original_label = label
                        elif original_label != label:
                            print 'Weird instance'
                            
                        if unicode(original_label) not in versus_labels:
                            continue
                        
                        
                        
                        if not ((tuple(versus_labels), original_label)
                             in histogram_bin[feature_type]):
                            histogram_bin[feature_type][(tuple(versus_labels), 
                                                         original_label)] = defaultdict(int)
                        bin_index = self.get_bin(svm_value)
                        histogram_bin[feature_type][(tuple(versus_labels), 
                                                     original_label)][bin_index]+=1
                    
                    label_count[feature_type][original_label] += 1
        return label_count, histogram_bin
    
    def get_histogram_all_files( self , reclassify_directory  ):
        statistic_files = glob.glob( os.path.join( reclassify_directory , '*%s' % RECLASSIFY_SUFFIX))
        self.total_histogram = {}
        self.prior = {}
        for statistic_file in statistic_files:
            label_count, histogram_bin = self.get_histogram( statistic_file )
            
            for feature_type in label_count:
                if not feature_type in self.prior:
                    self.prior[feature_type] = defaultdict(float)
                for original_label in label_count[feature_type]:
                    self.prior[feature_type][original_label] +=\
                     label_count[feature_type][original_label] 
            
            for feature_type in histogram_bin:
                if not feature_type in self.total_histogram:
                    self.total_histogram[feature_type] = {}
                for label in histogram_bin[feature_type]:
                    if not str(label) in self.total_histogram[feature_type]:
                        self.total_histogram[feature_type][str(label)] = defaultdict(int)
                    for bin_index in histogram_bin[feature_type][label]:
                        self.total_histogram[feature_type][str(label)][bin_index] +=\
                         histogram_bin[feature_type][label][bin_index]
        self._sum_histogram()
        self._normalize_prior()
    
    def _sum_histogram(self):
        self.sum_histogram = {}
        for feature_type in self.total_histogram:
            self.sum_histogram[feature_type] = {}
            for label in self.total_histogram[feature_type]:
                self.sum_histogram[feature_type][label] = 0
                for bin_index in self.total_histogram[feature_type][label]:
                    self.sum_histogram[feature_type][label] +=\
                     self.total_histogram[feature_type][label][bin_index]
    
    def _normalize_prior(self):
        self.normalized_prior = {}
        for feature_type in self.prior:
            self.normalized_prior[feature_type] = {}
            sum = 0
            for original_label in self.prior[feature_type]:
                sum += self.prior[feature_type][original_label]
            for original_label in self.prior[feature_type]:
                self.normalized_prior[feature_type][original_label] =\
                 self.prior[feature_type][original_label]/sum
    
    
    @classmethod
    def load_histogram(cls, summary_file):
        cls.instance = Histogram()
        with open(summary_file, 'r') as summary_file:
            temp = json.load( summary_file)
            cls.instance.total_histogram = temp[TOTAL_HISTOGRAM]
            cls.instance.prior = temp[PRIOR]
            cls.instance.bin_step = temp[BIN_STEP]
        cls.instance._sum_histogram()
        cls.instance._normalize_prior()
        return cls.instance
    
    def dump_into_file (self, summary_file):
        with open(summary_file, 'w') as summary_file:
            json.dump( {BIN_STEP: self.bin_step, 
                        TOTAL_HISTOGRAM: self.total_histogram,
                        PRIOR: self.prior}, 
                      summary_file)
        
    def get_bin (self, value):
        if value > 0:
            bin_index = math.ceil(float(value)/self.bin_step)
        elif value < 0:
            bin_index = math.floor(float(value)/self.bin_step)
        else:
            bin_index = 1
        return bin_index

    def get_probability(self, versus_labels, feature_type, 
                        target_label, target_value ):
        """
        P(  -2.1010391 | versus_labels = ('AFTER', 'BEFORE'),target_label = BEFORE )
        versus_labels = ('AFTER', 'BEFORE')
        target_label = 'BEFORE'
        target_value = -2.1010391
        """
        if not str((versus_labels, target_label)) in self.total_histogram[feature_type]:
            return 0
        bin_index = str(self.get_bin (target_value))
        if bin_index in self.total_histogram[feature_type][str((versus_labels, target_label))]:
            pass
        else:
            return 0
#             if bin_index > 0:
#                 bin_index = max(self.total_histogram[feature_type][str((versus_labels, target_label))].keys())
#             else:
#                 bin_index = min(self.total_histogram[feature_type][str((versus_labels, target_label))].keys())
        return (float((self.total_histogram[feature_type][str((versus_labels, target_label))][bin_index])) 
                    / self.sum_histogram[feature_type][str((versus_labels, target_label))])
    
    def get_probability_vector(self, result_vector, 
                               feature_type, target_label ):
        """
         P( result_vector | label ) = P(  -2.1010391 | classifier = ('AFTER', 'BEFORE'), 
                                                        label = BEFORE )
                                    x P(  -1.7459796 | classifier = ('SIMULTANEOUS', 'BEFORE'), 
                                                        label = BEFORE )
        {"('SIMULTANEOUS', 'AFTER')": 2.5173214, 
        "('AFTER', 'BEFORE')": -2.2637307, 
        "('SIMULTANEOUS', 'BEFORE')": -0.94173988}
        """
        
        product = 1
        target_label_included = False
        for versus_labels in result_vector:
            tokened_versus_labels = re.findall("'(\w+)'", versus_labels)
            if unicode(target_label) in tokened_versus_labels:
                target_label_included = True
                product *= self.get_probability( tuple(tokened_versus_labels), feature_type,
                                                 unicode(target_label) , 
                                                 result_vector[versus_labels] )
        if target_label_included:
            return product
        else:
            return 0
    
    def get_probability_label(self, feature_type, label):
        return self.normalized_prior[feature_type][label]
            
    def get_prior(self):
        return self.normalized_prior

"""
Those code will be commented when svm_histogram is moved to 
ttk
"""
GOLD_RECLASSIFY_DIRECTORY = 'gold_reclassify_result'
SILVER_RECLASSIFY_DIRECTORY = 'silver_reclassify_result'
# svm = Histogram(0.25)
# svm.get_histogram_all_files(GOLD_RECLASSIFY_DIRECTORY)
# svm.dump_into_file('gold_reclassify_statistic.stat')
# svm.get_histogram_all_files(SILVER_RECLASSIFY_DIRECTORY)
# svm.dump_into_file('silver_reclassify_statistic.stat')