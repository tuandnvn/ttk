from library.relation import get_standard
from library.classifier.classifier_ordering_loader import ClassifierRuleDictionary as crd
from docmodel.xml_parser import Parser
from docmodel.xml_parser import XmlDocElement, XmlDocument
from nltk.corpus import wordnet as wn

def check_event_pair_in_doc(file):
    xmldoc = Parser().parse_file(open(file, "r"))
    checker = crd()
    
    verb_events = []
    for element in xmldoc:
        if (element.tag == 'EVENT' and element.is_opening_tag()):
            prev_lex = element
            while prev_lex.tag != 'lex':
                prev_lex = prev_lex.previous
            if prev_lex.attrs['pos'][:2] == 'VB':
                if len(wn.synsets(element.next.content, 'v')) > 0:
                    verb_event = wn.synsets(element.next.content, 'v')[0].lemma_names[0]
                    verb_events.append(verb_event)
    print verb_events
    pair_in_database_counter = 0
    pair_in_database = []
    pair_in_database_with_some_certainty = []
    
    print 'Number of verb events : ' + str(len(verb_events))
    
    no_of_verb_events = len(verb_events)
    for i in xrange(no_of_verb_events):
        print i
        for j in xrange(i + 1, no_of_verb_events):
            v_1 = verb_events[i]
            v_2 = verb_events[j]
            if v_1 == v_2:
                continue
            try:
                result = checker.check_in_database(v_1, v_2)
                if result != None:
                    pair_in_database_counter += 1
                    pair_in_database.append((v_1, v_2, result))
                    if result[0] > 3 * result[1] or result[1] > 3 * result[0]:
                        pair_in_database_with_some_certainty.append((v_1, v_2, result))
            except Exception:
                print 'EXCEPTION'
    print 'Number of pairs in database : ' + str(len(pair_in_database))
    print 'Percentage :' + str(float(len(pair_in_database))/(no_of_verb_events*(no_of_verb_events-1)/2) * 100) + '%'
    print 'Number of pairs in database with some certainty of order : ' + str(len(pair_in_database_with_some_certainty))
    print 'Percentage :' + str(float(len(pair_in_database_with_some_certainty))/(no_of_verb_events*(no_of_verb_events-1)/2) * 100) + '%'
    
check_event_pair_in_doc('data/testfile.xml')
