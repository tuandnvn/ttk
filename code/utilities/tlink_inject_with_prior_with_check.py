import json
from ttk_path import TTK_ROOT
from docmodel.xml_parser import Parser
from library.tlink_relation import reverse
from library.timeMLspec import TID, EIID, NO_RELATION,\
                                EVENT, EID, MORPHY_LEMMA,\
                                INSTANCE, SYNSET_LEMMA, \
                                EVENTID, TLINK, \
                                EVENT_INSTANCE_ID, LID, \
                                RELATED_TO_EVENT_INSTANCE, RELTYPE
from library.classifier.classifySpec import EE_FLAG_MAIN_INTER_SENT,\
                                            EE_FLAG_MAIN_INTRA_SENT
from library.tlink_relation import BEFORE, AFTER, SIMULTANEOUS, NORELATION
from library.classifier.svm_histogram import Histogram
from library.classifier.classifier_ordering_loader import ClassifierRuleDictionary as CRD 
import math, os
from nltk.corpus import wordnet as wn
import logging
import itertools

logging.basicConfig(filename=os.path.join(TTK_ROOT, 'data', 'logs', 
                                          'incorporate_link_with_prior_with_check.log'),
                    level=logging.DEBUG)

"""
This file is a modification of 
incorporate_tlink.py, adopting code from
compare_performance.py, the purpose is to
inject result from result file into the no_tlink files,
with modification of result based on prior obtained from
event-pair.
The algorithm is as following:
- Calculate P ( lemma_pair | label ) with label = [BEFORE, AFTER, *SIMULTANEOUS]
    Could be calculated directly by the number of pairs in the 
    narrative scheme, or by doing a smoothing step.
    P ( lemma_pair | SIMULTANEOUS ) is set == 1/2N where N is the total 
    number of pair line in the corpus. (2 because lemma pair could be
    swapped).
    
- Calculate P ( result_vector | label ) with label = [BEFORE, AFTER, SIMULTANEOUS]
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
        
- Calculate P ( label | lemma_pair, result_vector ) ~ P(label) 
                                                x P ( result_vector | label )
                                                x P ( lemma_pair | label )
    following Naive Bayes method, given that we assume lemma pair and 
    result_vectors are independent features.
- Inject back the TLINK with the result label received from the aforementioned
    method.
"""

SVM_CLASSIFIER_ORIGIN = 'TreeSvm Classifier'
RESULT_DICT = 'Result_dict'
VOTE_DICT = 'Vote_dict'
TLINK_IDS_DICT = 'Tlink_dict'
SVM_HISTOGRAM_FILE = os.path.join( TTK_ROOT, 'library', 'classifier',
                                   'svm_histogram', 'reclassify_statistic_0_25.stat')

histogram = Histogram(0.25)
histogram.load_histogram(SVM_HISTOGRAM_FILE)

crd = CRD.get_single_instance()

def tlink_inject_with_prior_with_check( no_tlink_file , result_file, tlink_file , original_file):
    """
    """
    
    """
    Verb event should be a dictionary to map between
    an event id and some other lemmas generated from the 
    initial lemma. 
    """
    verb_events = {}
    """
    EVENT tag sample
    <EVENT class="OCCURRENCE" eid="e1000028">
    """
    xml_document = Parser().parse_file(open(no_tlink_file, "r"))
    xmldoc_original = Parser().parse_file(open(original_file, "r"))
    
    for element in xml_document.get_tags(EVENT):
        if element.is_opening_tag():
            eid = element.attrs[EID]
            event_content = element.next.content
            synsets_event = None
            if len(wn.synsets(event_content, 'v')) > 0:
                synsets_event = wn.synsets(element.next.content, 'v')[0].lemma_names
            verb_morphy = wn.morphy(event_content, 'v')
            
            verb_events[eid] = {MORPHY_LEMMA: verb_morphy, 
                                SYNSET_LEMMA: synsets_event}
    """
    <MAKEINSTANCE eventID="e2" polarity="POS" pos="VERB" eiid="ei2" 
    tense="PRESENT" aspect="PERFECTIVE">
    """
    verb_event_instance = {}
    for element in xml_document.get_tags(INSTANCE):
        if element.is_opening_tag():
            eiid = element.attrs[EIID]
            eid = element.attrs[EVENTID]
            if eid in verb_events:
                verb_event_instance[eiid] = verb_events[eid]
                
    """
    All TLINKs in the original document between two events
    Because excepts the TLINKs parts, original and classified 
    documents should be identical, so they could use the same 
    verb_event_instance.
    """
    original_ee_tlinks = {}
    for element in xmldoc_original.get_tags(TLINK):
        # keep track of event order here
        if element.is_opening_tag():
            lid = element.attrs[LID]
            if EVENT_INSTANCE_ID in element.attrs:
                eiid = element.attrs[EVENT_INSTANCE_ID]
                if RELATED_TO_EVENT_INSTANCE in element.attrs:
                    reiid = element.attrs[RELATED_TO_EVENT_INSTANCE]
                    if RELTYPE in element.attrs:
                        if eiid in verb_event_instance and reiid in verb_event_instance:
                            original_ee_tlinks[(eiid, reiid)]= (lid, element.attrs[RELTYPE])
                
    with open(result_file, 'r') as  result_file:
        label_vote_dict = json.load( result_file)
    
    fix_label_counter = 0
    worsen_label_counter = 0
    for feature_type in label_vote_dict:
        for line_counter in label_vote_dict[feature_type]:
            result_dict =  label_vote_dict[feature_type][line_counter][RESULT_DICT]
            label_vote = label_vote_dict[feature_type][line_counter][VOTE_DICT]
            ids = label_vote_dict[feature_type][line_counter][TLINK_IDS_DICT]
            
            raw_relType = label_vote[-1][0]
            """
            Have to re calculate the relType here
            - Calculate P ( label | lemma_pair, result_vector ) ~ P(label) 
                                                x P ( result_vector | label )
                                                x P ( lemma_pair | label )
            """
#             if raw_relType == NORELATION or raw_relType == SIMULTANEOUS:
            if raw_relType == NORELATION:
                pass
            else:
                def check_event_pair(ids):
                    for id in ids:
                        if id[1]== TID:
                            return False
                    return True
                
                """
                If the relation is between event pairs, we check 
                the narrative scheme, else, just use the raw_relType
                for TLink between time and event.
                """
                new_ids = {}
                for id in ids:
                    if id[1] in [TID, EIID]:
                        new_ids[id[0]] = id[2]
                
                original_relation = None
                if (new_ids['0'], new_ids['1']) in original_ee_tlinks:
                    original_relation = original_ee_tlinks[(new_ids['0'], new_ids['1'])][1]
                elif (new_ids['1'], new_ids['0']) in original_ee_tlinks:
                    original_relation = reverse(original_ee_tlinks
                                                [(new_ids['1'], new_ids['0'])][1])
                """
                Eleventh try
                Only consider main event pairs inter sentences 
                """
                if check_event_pair(ids):
                    probability = {}
                    max_label = None
                    max_prob = None
                    
                    """
                    Third approach: only consider labels inside the votes
                    """
                    result_prob = {}
                    label_prob = {}
                    lemma_pair_prob = {}
                    for label in [str(label[0]) for label in label_vote]:
                        if not label in [BEFORE, AFTER, SIMULTANEOUS]:
                            continue
                        """
                        15th try: only fix BEFORE and AFTER labels
                        """
#                         if not label in [BEFORE, AFTER]:
#                             continue
#                     for label in [BEFORE, AFTER, SIMULTANEOUS]:
                        probability[label] = 1
                        
                        
                        result_prob[label] = histogram.get_probability_vector(result_dict, label)
                        probability[label] *= result_prob[label]
                        
                        """
                        First approach: only use the morphy lemma
                        """
                        morphy_1 = verb_event_instance[new_ids['0']][MORPHY_LEMMA]
                        morphy_2 = verb_event_instance[new_ids['1']][MORPHY_LEMMA]
#                         lemma_pair_prob[label] = crd.get_lemma_pair_prob((morphy_1,morphy_2,label))
#                         lemma_pair_prob[label] = crd.get_lemma_pair_prob_smoothing((morphy_1,morphy_2),label)
                        
                        """
                        Tenth approach: desperate try, multiply all of them together
                        """
#                         probability[label] *= lemma_pair_prob[label]
                        """
                        Done first approach
                        """
                        
                        """
                        Second approach: use all pairs of lemmas with lemma
                        in corresponding two synsets
                        """
                        lemma_pair_prob[label] = 0
                        synset_1 = verb_event_instance[new_ids['0']][SYNSET_LEMMA]
                        synset_2 = verb_event_instance[new_ids['1']][SYNSET_LEMMA]
                        if synset_1 != None and synset_2 != None:
                            for l_1, l_2 in itertools.product(synset_1, synset_2):
                                lemma_pair_prob[label] += crd.get_lemma_pair_prob_smoothing((l_1,l_2),label)
#                                 lemma_pair_prob[label] += crd.get_lemma_pair_prob((l_1,l_2),label)
                        
                        """
                        Done second approach
                        """
                        
                        
                        """
                        Seventh try: turn off lemma pairs
                        """
                        probability[label] *= lemma_pair_prob[label]
                        
                        label_prob[label] = histogram.get_probability_label (label)
                        
#                         """
#                         14th try: normalize BEFORE and AFTER labels
#                         """
#                         if label == BEFORE or label == AFTER:
#                             label_prob[label] = (histogram.get_probability_label (BEFORE)
#                                                   + histogram.get_probability_label (AFTER))/2
                            
                        """
                        13 rd try: disable label prob
                        """    
                        probability[label] *= label_prob[label]
                        
                        if max_prob == None or max_prob < probability[label]:
                            max_prob = probability[label]
                            max_label = label
                    
                    """
                    Forth try:
                    if max_prob == 0, it means that all probabilities = 0
                    and we should follow the initialy vote
                    """
                    if max_prob == 0:
                        relType = raw_relType
                    else:
                        relType = max_label
                    
                    need_to_keep_track = False
                    if (relType == raw_relType and original_relation != None
                        and original_relation != relType
                        and original_relation in [BEFORE, AFTER, SIMULTANEOUS]):
                        need_to_keep_track = True
                        logging.info('---------------DOESNT HELP----------------')
                        
                    if relType != raw_relType and original_relation != None:
                        need_to_keep_track = True
                        if ( original_relation == relType ):
                            fix_label_counter += 1
                        if ( original_relation == raw_relType ):
                            worsen_label_counter += 1
                        logging.info('---------------MAKE CHANGE----------------')
                    
                    if need_to_keep_track:
                        logging.info('Correct relation : %s' % original_relation)
                        logging.info('Original classified : %s' % raw_relType)
                        logging.info('Prior classified : %s' % relType)
                        logging.info(morphy_1)
                        logging.info(morphy_2)
                        logging.info(synset_1)
                        logging.info(synset_2)
                        logging.info('--result_prob--')
                        logging.info(result_prob)
                        logging.info('--label_prob--')
                        logging.info(label_prob)
                        logging.info('--lemma_pair_prob--')
                        logging.info(lemma_pair_prob)
                        logging.info(probability)
                        logging.info('==============================')
                else:
                    relType = raw_relType
                
                xml_document.add_tlink(relType, new_ids['0'],
                                new_ids['1'], SVM_CLASSIFIER_ORIGIN)
    
    xml_document.save_to_file (tlink_file)
    return (fix_label_counter, worsen_label_counter)