from ttk_path import TTK_ROOT
from docmodel.xml_parser import Parser
from library.tlink_relation import BEFORE, AFTER, SIMULTANEOUS
from library.tlink_relation import reverse
from library.timeMLspec import EVENT, INSTANCE, TIMEX, EE, ET,\
                            EID, EVENTID, TLINK, \
                            EVENT_INSTANCE_ID, TIME_ID, \
                            RELATED_TO_EVENT_INSTANCE, \
                            RELATED_TO_TIME, RELTYPE, \
                            NO_RELATION
import logging, os, glob

logging.basicConfig(filename=os.path.join(TTK_ROOT, 'data', 'logs', 
                                          'checking_abnormal.log'),
                    level=logging.DEBUG)

ADD_TLINK_SUFFIX = '.tml'
ADDED_TLINK_DIRECTORY = os.path.join(TTK_ROOT, 'data', 'added_tlink')
"""
Abnormal checking logic:
3 relations:
    event 0 is main, related to event 1
    event 0 is main, related to dct time
    dct time is main, related to event 1
if event 0 is BEFORE event 1:
    other doesn't has BEFORE => wrong
if event 0 is AFTER event 1:
    other doesn't has AFTER => wrong
if event 0 is SIMULTANEOUS event 1:
    if other has one SIMULTANEOUS, the other also SIMULTANEOUS
Better using a composition:
                AFTER                 BEFORE                 SIMULTANEOUS
AFTER            AFTER                *                          AFTER
BEFORE           *                   BEFORE                      BEFORE
SIMULTANEOUS     AFTER               BEFORE                      SIMULTANEOUS
"""
LOGIC_COMPOSITION = {
                     (AFTER,            AFTER):         [AFTER],
                     (AFTER,            BEFORE):        [AFTER, BEFORE, SIMULTANEOUS],
                     (AFTER,            SIMULTANEOUS):  [AFTER],
                     (BEFORE,           AFTER):         [AFTER, BEFORE, SIMULTANEOUS],
                     (BEFORE,           BEFORE):        [BEFORE],
                     (BEFORE,           SIMULTANEOUS):  [BEFORE],
                     (SIMULTANEOUS,     AFTER):         [AFTER],
                     (SIMULTANEOUS,     BEFORE):        [BEFORE],
                     (SIMULTANEOUS,     SIMULTANEOUS):  [SIMULTANEOUS]
                    }
def check_abnormal_single(tlink_file):
    xml_document = Parser().parse_file(open(tlink_file, "r"))
    
    ee_tlinks = []
    """
    It doesn't ensure that any event that
    has a TLINK with the dct time need to be 
    the main event in a sentence, but it's correct
    for the classified tlinks.
    """
    main_events = {}
    for element in xml_document.get_tags(TLINK):
        # keep track of event order here
        if element.is_opening_tag():
            if EVENT_INSTANCE_ID in element.attrs:
                eid = element.attrs[EVENT_INSTANCE_ID]
                if RELATED_TO_EVENT_INSTANCE in element.attrs:
                    reid = element.attrs[RELATED_TO_EVENT_INSTANCE]
                    if RELTYPE in element.attrs:
                        ee_tlinks.append((eid, reid, element.attrs[RELTYPE]))
                if RELATED_TO_TIME in element.attrs:
                    rtid = element.attrs[RELATED_TO_TIME]
                    if RELTYPE in element.attrs:
                        if rtid == 't0':
                            """
                            Reverse the relation and the position of 
                            time and event so as the timeid is always
                            the main entity
                            """
                            main_events[eid] = (reverse(element.attrs[RELTYPE]))
            if TIME_ID in element.attrs:
                tid = element.attrs[TIME_ID]
                if RELATED_TO_EVENT_INSTANCE in element.attrs:
                    reid = element.attrs[RELATED_TO_EVENT_INSTANCE]
                    if RELTYPE in element.attrs:
                        if tid == 't0':
                            main_events[reid] = (element.attrs[RELTYPE])
    
    total_number = 0
    wrong_number = 0
    for ee_tlink in ee_tlinks:
        if ee_tlink[0] in main_events and ee_tlink[1] in main_events:
            total_number += 1
            """
            They are all main events
            Relations between main events: AFTER, BEFORE and SIMULTANEOUS
            Relations between main event and dct time: AFTER, BEFORE and SIMULTANEOUS
            """
            logging.info("=========================================")
            logging.info(ee_tlink[0])
            logging.info(ee_tlink[1])
            """
            event 0 is main, related to dct time
            """
            relation_1 = reverse(main_events[ee_tlink[0]])
            logging.info(relation_1)
            """
            dct time is main, related to event 1
            """
            relation_2 = main_events[ee_tlink[1]]
            logging.info(relation_2)
            """
            event 0 is main, related to event 1
            """
            relation_3 = ee_tlink[2]
            logging.info(relation_3)
            if relation_3 in LOGIC_COMPOSITION[(relation_1, relation_2)]:
                logging.info("Satisfy constraint")
            else:
                wrong_number += 1
                logging.warn("DOESN'T SATISFY")
    logging.info("Wrong number %d/ Total %d" %(wrong_number, total_number))
    return (wrong_number, total_number)
    
def check_abnormal( tlink_directory ):
    tlink_files = glob.glob(os.path.join(tlink_directory, 
                                            '*%s' % ADD_TLINK_SUFFIX))
    overall_wrong_number = 0
    overall_total_number = 0
    for tlink_file in tlink_files:
        (wrong_number, total_number) = check_abnormal_single(tlink_file)
        overall_wrong_number += wrong_number
        overall_total_number += total_number
    logging.info("Overal, Wrong number %d/ Total %d" %
                 (overall_wrong_number, overall_total_number))

check_abnormal ( ADDED_TLINK_DIRECTORY )