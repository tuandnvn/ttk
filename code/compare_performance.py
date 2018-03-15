from ttk_path import TTK_ROOT
from library.tlink_relation import reverse
from library.classifier.classifier_ordering_loader import ClassifierRuleDictionary as crd
from docmodel.xml_parser import Parser
from docmodel.xml_parser import XmlDocElement, XmlDocument
from nltk.corpus import wordnet as wn
import logging, os, glob
import time, itertools
from library.timeMLspec import EVENT, EID, EIID,\
                                INSTANCE, RELATED_TO_EVENT_INSTANCE,\
                                RELTYPE, EVENTID, TLINK, \
                                EVENT_INSTANCE_ID, LID, \
                                MORPHY_LEMMA, SYNSET_LEMMA

logging.basicConfig(filename=os.path.join(TTK_ROOT, 'data', 'logs', 
                                          'compare_performance.log'),
                    level=logging.DEBUG)

ADD_TLINK_SUFFIX = '.tml'
ORIGINAL_SUFFIX = '.tml'
ADDED_TLINK_DIRECTORY = os.path.join(TTK_ROOT, 'data', 'added_tlink')
TEST_DIRECTORY  = os.path.join(TTK_ROOT, 'data', 'in', 
                                'te3-platinumstandard', 'te3-platinum')

narrative_checker = crd()
narrative_checker.read_lexical_rules_into_dict()
# narrative_checker.read_lexical_rules()

def compare_performance_single( tlink_file, original_file ):
    logging.info('================Compare======================')
    logging.info('Classified file: %s' %tlink_file)
    logging.info('Original file: %s' %original_file)
    """
    Compare the performance of a classified file (that is the result of 
    any algorithm or method), toward a destination gold file and the 
    event pair temporal ordering provided by narrative scheme database. 
    
    Only compare the performance between classified files, 
    original files, and temporal ordering database with TLINKs
    that is:
        - TLINKS between two events.
        - Two events need to appear in both original file
        and classified file
        - Two events need to be found in the narrative scheme.
    """
    xmldoc_classified = Parser().parse_file(open(tlink_file, "r"))
    xmldoc_original = Parser().parse_file(open(original_file, "r"))
    
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
    for element in xmldoc_classified.get_tags(EVENT):
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
    for element in xmldoc_classified.get_tags(INSTANCE):
        if element.is_opening_tag():
            eiid = element.attrs[EIID]
            eid = element.attrs[EVENTID]
            if eid in verb_events:
                verb_event_instance[eiid] = verb_events[eid]
            
    """
    All TLINKS in the document that are of two events
    """
    ee_tlinks = []
    for element in xmldoc_classified.get_tags(TLINK):
        # keep track of event order here
        if element.is_opening_tag():
            lid = element.attrs[LID]
            if EVENT_INSTANCE_ID in element.attrs:
                eiid = element.attrs[EVENT_INSTANCE_ID]
                if RELATED_TO_EVENT_INSTANCE in element.attrs:
                    reiid = element.attrs[RELATED_TO_EVENT_INSTANCE]
                    if RELTYPE in element.attrs:
                        if eiid in verb_event_instance and reiid in verb_event_instance:
                            ee_tlinks.append((eiid, reiid, (lid, element.attrs[RELTYPE])))
    
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
    
    no_of_pair_in_database = 0
    no_of_pair = 0
    """
    No of pairs of events that are found in
    classified files, original files and narrative scheme.
    """
    no_of_compare_pairs = 0
    """
    No of pairs of events that are found in
    classified files, original files and narrative scheme
    and that doesn't have matching relation type between
    classified and original files
    """
    no_of_incompatible_pairs = 0
    
    no_of_verb_events = len(verb_events)
    
    for eiid, reiid, tlink in ee_tlinks:
        no_of_pair += 1
        """
        Here accessing verb_event_instance given the event instance id
        would give the result to be a dictionary of lemmas.
        """
        lemma_dict_1 = verb_event_instance[eiid]
        lemma_dict_2 = verb_event_instance[reiid]
        
        logging.info("---------------------------------------------------------------")
        logging.info("---------Classified file---------")
        logging.info("Tlink id in classified file is %s" %tlink[0])
        relType = tlink[1]
        logging.info("Label in classified file is %s" %relType)
        
        if (eiid, reiid) in original_ee_tlinks:
            no_of_compare_pairs += 1
            original_relation = original_ee_tlinks[(eiid, reiid)][1]
            logging.info("---------Original file---------")
            logging.info("Tlink id in classified file is %s" 
                         %original_ee_tlinks[(eiid, reiid)][0])
            logging.info("Label in classified file is %s" 
                         %original_relation)
            if relType != original_relation:
                no_of_incompatible_pairs += 1
        elif (reiid, eiid) in original_ee_tlinks:
            no_of_compare_pairs += 1
            original_relation = reverse(original_ee_tlinks[(reiid, eiid)][1])
            logging.info("---------Original file---------")
            logging.info("In the original file, the TLINK is %s" 
                         %original_relation)
            logging.info("Tlink in original file %s" 
                         %original_ee_tlinks[(reiid, eiid)][0])
            if relType != original_relation:
                no_of_incompatible_pairs += 1
        else:
            continue
        
        logging.info("---------LEMMA---------")
        if lemma_dict_1[MORPHY_LEMMA] != None and lemma_dict_2[MORPHY_LEMMA] != None:
            v_1 = lemma_dict_1[MORPHY_LEMMA]
            v_2 = lemma_dict_2[MORPHY_LEMMA]
            
            if v_1 == v_2:
                continue
            try:
                result = narrative_checker.check_in_dict(v_1, v_2)
                if result != None:
                    logging.info("%s, %s, %d, %d" %(v_1, v_2, 
                                                    result[0], result[1]))
            except Exception as e:
                logging.error(str(e))
        
        logging.info("---------SYNSET---------")
        sum_result = [0,0]
        if lemma_dict_1[SYNSET_LEMMA] != None and lemma_dict_2[SYNSET_LEMMA] != None:
            v_1_list = lemma_dict_1[SYNSET_LEMMA]
            v_2_list = lemma_dict_2[SYNSET_LEMMA]
            
            for v_1, v_2 in itertools.product(v_1_list, v_2_list):
                if v_1 == v_2:
                    continue
                try:
                    result = narrative_checker.check_in_dict(v_1, v_2)
                    if result != None:
                        sum_result[0] += result[0]
                        sum_result[1] += result[1]
                except Exception as e:
                    logging.error(str(e))
            logging.info("%s\n %s\n %d, %d" %(str(v_1_list), str(v_2_list), 
                                            sum_result[0], sum_result[1]))
            
        no_of_pair_in_database += 1
            
    logging.info('Number of events tlink: %d' % no_of_pair )
    logging.info('Number of pairs in database : %d' % no_of_pair_in_database)
    logging.info('Percentage of pairs that are found \
                in narrative scheme database: %.2f' % (float(no_of_pair_in_database)/no_of_pair))
    logging.info('Number of pairs that are found in database\
                and original files as well %d' %no_of_compare_pairs)
    logging.info('Number of pairs that are found in database\
                and original files and not compatible %d' %no_of_incompatible_pairs)
    logging.info('============================================================')
    
def compare_performance( tlink_directory, original_directory ):
    tlink_files = glob.glob(os.path.join(tlink_directory, 
                                            '*%s' % ADD_TLINK_SUFFIX))
    for tlink_file in tlink_files:
        rel_filename = tlink_file[tlink_file.rindex(os.path.sep) + 1:]
        original_file = os.path.join(original_directory,
                                       '%s%s' % (rel_filename[:-len(ADD_TLINK_SUFFIX)],
                                    ORIGINAL_SUFFIX) )
        compare_performance_single(tlink_file, original_file)

# begin_time = time.time()
# compare_performance ( ADDED_TLINK_DIRECTORY, TEST_DIRECTORY )
# logging.info("Total time %d: " % ( time.time() - begin_time))

# print narrative_checker.check_in_dict('die', 'help')
# print narrative_checker.check_in_dict('help', 'die')
# print narrative_checker.get_lemma_pair_prob(('help', 'die'), 'BEFORE')
# print narrative_checker.get_lemma_pair_prob(('help', 'die'), 'AFTER')
# print narrative_checker.get_lemma_pair_prob(('help', 'die'), 'SIMULTANEOUS')
# print narrative_checker.get_lemma_pair_prob(('die', 'help'), 'SIMULTANEOUS')