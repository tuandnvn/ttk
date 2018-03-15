import json
from docmodel.xml_parser import Parser
from library.timeMLspec import TID, EIID, NO_RELATION

"""
Result file has the following format
{"main_events_in_consecutive_sentences": {
"1": [[["AFTER", [1, 0.66257153]], 
    ["BEFORE", [2, 1.99997655]]], 
    [["0", "eid", "e3"], ["0", "eiid", "ei3"],
     ["1", "eid", "e6"], ["1", "eiid", "ei6"]]]
     }}
"""


SVM_CLASSIFIER_ORIGIN = 'TreeSvm Classifier'
VOTE_DICT = 'Vote_dict'
TLINK_IDS_DICT = 'Tlink_dict'

def tlink_inject( no_tlink_file , result_file, tlink_file ):
    xml_document = Parser().parse_file(open(no_tlink_file, "r"))
    
    with open(result_file, 'r') as  result_file:
        label_vote_dict = json.load( result_file)
    for feature_type in label_vote_dict:
        print feature_type
        print len(label_vote_dict[feature_type].keys())
        for line_counter in label_vote_dict[feature_type]: 
            label_vote = label_vote_dict[feature_type][line_counter][VOTE_DICT]
            ids = label_vote_dict[feature_type][line_counter][TLINK_IDS_DICT]
            relType = label_vote[-1][0]
            
            new_ids = {}
            for id in ids:
                if id[1] in [TID, EIID]:
                    new_ids[id[0]] = id[2]
            
            if relType != NO_RELATION:
                xml_document.add_tlink(relType, new_ids['0'],
                                    new_ids['1'], SVM_CLASSIFIER_ORIGIN)
    
    xml_document.save_to_file (tlink_file)
    
def tlink_remove( original_file, no_tlink_file ):
    xml_document = Parser().parse_file(open(original_file, "r"))
    xml_document.remove_tags('TLINK')
    xml_document.save_to_file (no_tlink_file)