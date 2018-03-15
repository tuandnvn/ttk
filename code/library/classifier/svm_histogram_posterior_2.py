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

"""
A modified version of svm_histogram_posterior
but instead of using bin as the [-1,0], [0,1], using bins [-1.5, -0.5], [-.5, .5], [.5, 1.5]
"""
class Histogram:
    def __init__(self, bin_step = None):
        self.total_histogram = {}
        self.bin_step = bin_step
    
    @classmethod
    def get_singleton(cls):
        return cls.instance
        
        
    def get_histogram( self , statistic_file ):
        """
        [["SIMULTANEOUS", "AFTER"], "NORELATION", 0.36286006999999998], 
        [["AFTER", "BEFORE"], "NORELATION", -0.83785922000000002], 
        [["SIMULTANEOUS", "BEFORE"], "NORELATION", -0.12235496]]
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
                    versus_labels = []
                    svm_values = []
                    original_label = None
                    for versus_label, label, svm_value in result_instance:
                        if original_label == None:
                            original_label = label
                        elif original_label != label:
                            print 'Weird instance'
                        versus_labels.append(versus_label)
                        svm_values.append(svm_value)
                        
                    label_count[feature_type][original_label] += 1
                    label_group = []
                    for versus_label in versus_labels:
                        label_group.append(tuple(versus_label))
                    
                    if not (tuple(label_group) in histogram_bin[feature_type]):
                        histogram_bin[feature_type][tuple(label_group)] = {}
                    if not original_label in histogram_bin[feature_type][tuple(label_group)]:
                        histogram_bin[feature_type][tuple(label_group)][original_label] = defaultdict(int)
                    bin_indices = tuple([self.get_bin(value) for value in svm_values])
                    histogram_bin[feature_type][tuple(label_group)][original_label][bin_indices]+=1
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
                for label_group in histogram_bin[feature_type]:
                    if not str(label_group) in self.total_histogram[feature_type]:
                        self.total_histogram[feature_type][str(label_group)] = {}
                    
                    for label in histogram_bin[feature_type][label_group]:
                        if label not in self.total_histogram[feature_type][str(label_group)]:
                            self.total_histogram[feature_type][str(label_group)][label] = defaultdict(int)
                        
                        """
                        bin_index is a tuple of bin_index_1, bin_index_2
                        """
                        for bin_indices in histogram_bin[feature_type][label_group][label]:
                            self.total_histogram[feature_type][str(label_group)][label][str(bin_indices)] +=\
                             histogram_bin[feature_type][label_group][label][bin_indices]
        self._sum_histogram()
        self._normalize_prior()
    
    def _sum_histogram(self):
        self.sum_histogram = {}
        for feature_type in self.total_histogram:
            self.sum_histogram[feature_type] = {}
            for label_group in self.total_histogram[feature_type]:
                self.sum_histogram[feature_type][label_group] = 0
                for label in self.total_histogram[feature_type][label_group]:
                    for bin_indices in self.total_histogram[feature_type][label_group][label]:
                        self.sum_histogram[feature_type][label_group] +=\
                         self.total_histogram[feature_type][label_group][label][bin_indices]
    
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
        if value > self.bin_step / 2:
            bin_index = math.ceil(float(value - self.bin_step / 2)/self.bin_step)
        elif value < -self.bin_step / 2:
            bin_index = math.floor(float(value + self.bin_step / 2)/self.bin_step)
        else:
            bin_index = 0
        return bin_index
    
    def get_normalized_probability_vector(self, result_vector, 
                               feature_type ):
        all_considering_labels = set()
        for versus_labels in result_vector:
            tokened_versus_labels = re.findall("'(\w+)'", versus_labels)
            for label in tokened_versus_labels:
                all_considering_labels.add(label)
        count = {}
        count_sum = 0
        for label in all_considering_labels:
            count[label] = self.get_count_vector(result_vector, feature_type, label)
            count_sum += count[label]
        if count_sum == 0:
            for label in count:
                count[label] = float(1)/len(count)
        else:
            for label in count:
                count[label] = float(count[label])/ count_sum
        return count

    def get_count_vector(self, result_vector, 
                               feature_type, target_label ):
        """
         P(  label | result_vector ) 
         with result_vector is
        [("SIMULTANEOUS", "AFTER"),  -0.066669875000000003], 
        [["AFTER", "BEFORE"],  -0.75275745000000005], 
        [["SIMULTANEOUS", "BEFORE"], -0.74580245999999994]
        """
        key = []
        for versus_labels in result_vector:
            tokened_versus_labels = re.findall("'(\w+)'", versus_labels)
            key.append(tuple(tokened_versus_labels))
        
        for t in self.total_histogram[feature_type]:
            if sorted(key) == sorted(eval(t)):
                key = t
        
        target_label = unicode(target_label)
        
        
        bin_indices = []
        for versus_labels in result_vector:
            bin_indices.append(self.get_bin(result_vector[versus_labels]))
        bin_indices = unicode(tuple(bin_indices))
        
        if target_label in self.total_histogram[feature_type][key]:
            if bin_indices in self.total_histogram[feature_type][key][target_label]:
                return self.total_histogram[feature_type][key][target_label][bin_indices] 
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
svm = Histogram(1)
svm.get_histogram_all_files(GOLD_RECLASSIFY_DIRECTORY)
svm.dump_into_file('gold_reclassify_statistic_posterior_2.stat')
# svm.get_histogram_all_files(SILVER_RECLASSIFY_DIRECTORY)
# svm.dump_into_file('silver_reclassify_statistic_posterior.stat')