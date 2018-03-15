from ttk_path import TTK_ROOT
from collections import defaultdict
import glob
import json
import math
import os
import re
from library.tlink_relation import BEFORE, AFTER, SIMULTANEOUS
from numpy.core.fromnumeric import sum

# import logging
# logging.basicConfig(filename=os.path.join(TTK_ROOT, 'data', 'logs', 
#                                           'incorporate_link_with_prior.log'),
#                     level=logging.DEBUG)

RECLASSIFY_SUFFIX = '.reclassifiy' 
class Histogram:
    def __init__(self, bin_step):
        self.total_histogram = {}
        self.bin_step = bin_step
        
    def _sum_histogram(self):
        self.sum_histogram = {}
        for label in self.total_histogram:
            self.sum_histogram[label] = 0
            for bin_index in self.total_histogram[label]:
                self.sum_histogram[label] += self.total_histogram[label][bin_index]
                
    def load_histogram(self, summary_file):
        with open(summary_file, 'r') as summary_file:
            self.total_histogram = json.load( summary_file)
        self._sum_histogram()
    
    def get_histogram( self , statistic_file ):
        """
        [["SIMULTANEOUS", "AFTER"], "AFTER", 2.6686243]
        """
        histogram_bin = {}
        with open(statistic_file, 'r') as  statistic_file:
            statistic_list = json.load( statistic_file )
            for versus_labels, original_label, value in statistic_list:
                if not (tuple(versus_labels), original_label) in histogram_bin:
                    histogram_bin[(tuple(versus_labels), original_label)] = defaultdict(int)
                bin_index = self.get_bin(value)
                histogram_bin[(tuple(versus_labels), original_label)][bin_index]+=1
        return histogram_bin
    
    def get_histogram_all_files( self , reclassify_directory  ):
        statistic_files = glob.glob( os.path.join( reclassify_directory , '*%s' % RECLASSIFY_SUFFIX))
        self.total_histogram = {}
        for statistic_file in statistic_files[:3]:
            histogram_bin = self.get_histogram( statistic_file )
            for label in histogram_bin:
                if not str(label) in self.total_histogram:
                    self.total_histogram[str(label)] = defaultdict(int)
                for bin_index in histogram_bin[label]:
                    self.total_histogram[str(label)][bin_index] += histogram_bin[label][bin_index]
        self._sum_histogram()
    
    def dump_into_file (self, summary_file):
        with open(summary_file, 'w') as summary_file:
            json.dump( self.total_histogram, summary_file)
        
    def get_bin (self, value):
        if value > 0:
            bin_index = math.ceil(float(value)/self.bin_step)
        elif value < 0:
            bin_index = math.floor(float(value)/self.bin_step)
        else:
            bin_index = 1
        return bin_index

    def get_probability(self, versus_labels, target_label, target_value ):
        """
        P(  -2.1010391 | versus_labels = ('AFTER', 'BEFORE'),target_label = BEFORE )
        versus_labels = ('AFTER', 'BEFORE')
        target_label = 'BEFORE'
        target_value = -2.1010391
        """
        if not str((versus_labels, target_label)) in self.total_histogram:
            return 1
        bin_index = str(self.get_bin (target_value))
        if bin_index in self.total_histogram[str((versus_labels, target_label))]:
            pass
        else:
            if bin_index > 0:
                bin_index = max(self.total_histogram[str((versus_labels, target_label))].keys())
            else:
                bin_index = min(self.total_histogram[str((versus_labels, target_label))].keys())
        return (float((self.total_histogram[str((versus_labels, target_label))][bin_index])) 
                    / self.sum_histogram[str((versus_labels, target_label))])
    
    def get_probability_vector(self, result_vector, target_label ):
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
                product *= self.get_probability( tuple(tokened_versus_labels), unicode(target_label) , 
                                                 result_vector[versus_labels] )
        if target_label_included:
            return product
        else:
            return 0
    
    def get_probability_label(self, label):
        try:
            return self.prob_labels[label]
        except Exception:
            self.prob_labels = {}
            self.prob_labels[AFTER] = self.sum_histogram["((u'AFTER', u'BEFORE'), u'AFTER')"]
            self.prob_labels[BEFORE] = self.sum_histogram["((u'AFTER', u'BEFORE'), u'BEFORE')"]
            self.prob_labels[SIMULTANEOUS] = self.sum_histogram["((u'SIMULTANEOUS', u'BEFORE'), u'SIMULTANEOUS')"]
            
            prob_labels_sum = sum(self.prob_labels.values())
            for key in self.prob_labels:
                self.prob_labels[key] = float(self.prob_labels[key])/prob_labels_sum
            return self.prob_labels[label]
    
#histogram = Histogram(0.25)
#histogram.get_histogram_all_files(RECLASSIFY_RESULT_DIRECTORY)
#histogram.dump_into_file('reclassify_statistic.txt')
