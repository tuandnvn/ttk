from docmodel import xml_parser
from docmodel.xml_parser import Parser
from docmodel.xml_parser import XmlDocElement, XmlDocument
from library.tlink_relation import reverse
from library.timeMLspec import EVENT, INSTANCE, TIMEX, EE, ET,\
                            EID, EVENTID, TLINK, \
                            EVENT_INSTANCE_ID, TIME_ID, \
                            RELATED_TO_EVENT_INSTANCE, \
                            RELATED_TO_TIME, RELTYPE, \
                            NO_RELATION,  UNKNOWN_RELTYPE


def feature_recollect( doc , ee_file_name , et_file_name,
                       ee_file_name_adjacent, et_file_name_adjacent ):
    """
     Find training sample from ee file and et file that could be found in the parsed_file
     parsed_file: A TimeML file with POS tag, chunk tag (NG and VG), TIMEX3, EVENT and SIGNAL tags
     ee_file: ee_file that is the temporary ee file output from classifier module
     et_file: et_file that is the temporary et file output from classifier module
    
    <TLINK lid="l27" relatedToEventInstance="ei412" relType="BEFORE"
             eventInstanceID="ei410"></TLINK>
    <TLINK lid="l22" relatedToTime="t82" relType="BEFORE"
             eventInstanceID="ei405"></TLINK>
    """
    
    ee_dict = {}
    et_dict = {}
    
    tlinks = []
    
    # TODO: Need to check the pair of A, related_B in the correct order 
    # in the text file
    # because of the prior distribution of narrative ordering
    # If it not in the write order, it need to be switch, and RELTYPE
    # need to be reversed 
    # So when getting a pair of event/time, related event/time
    # if they're not in the right order, switch them,
    # and reverse TYPE
    
    for element in doc.get_tags(TLINK):
        # keep track of event order here
        if element.is_opening_tag():
            if EVENT_INSTANCE_ID in element.attrs:
                eid = element.attrs[EVENT_INSTANCE_ID]
                if RELATED_TO_EVENT_INSTANCE in element.attrs:
                    reid = element.attrs[RELATED_TO_EVENT_INSTANCE]
                    if RELTYPE in element.attrs:
                        tlinks.append((EE, eid, reid, element.attrs[RELTYPE]))
                if RELATED_TO_TIME in element.attrs:
                    rtid = element.attrs[RELATED_TO_TIME]
                    if RELTYPE in element.attrs:
                        tlinks.append((ET, eid, rtid, element.attrs[RELTYPE]))
            if TIME_ID in element.attrs:
                tid = element.attrs[TIME_ID]
                if RELATED_TO_EVENT_INSTANCE in element.attrs:
                    reid = element.attrs[RELATED_TO_EVENT_INSTANCE]
                    if RELTYPE in element.attrs:
                        tlinks.append((ET, tid, reid, element.attrs[RELTYPE]))
    
    # collect the instance so we can merge in the information when we
    # find and event.    
    instances = {}
    for instance in doc.get_tags(INSTANCE):
        eid = instance.attrs.get(EVENTID, None)
        instances[eid] = instance
    
    # could put the check here
    # so to make sure that pairs in using_dict
    # is always in the right narrative order
    
    tid_and_eiid = doc.collect_tid_and_eiid()
    tid_and_eiid_dict = {}
    for i in xrange(len(tid_and_eiid)):
        tid_and_eiid_dict[tid_and_eiid[i]] = i
    for type, id, rid, relType in tlinks:
        using_dict = None
        if (type == EE):
            using_dict = ee_dict 
        elif (type == ET):
            using_dict = et_dict
        
        if id in tid_and_eiid_dict and rid in tid_and_eiid_dict:
            if tid_and_eiid_dict[id] < tid_and_eiid_dict[rid]:
                # In the right order
                using_dict[id  + ' ' + rid] = relType
            elif tid_and_eiid_dict[id] > tid_and_eiid_dict[rid]:
                # In the right order
                using_dict[rid  + ' ' + id] = reverse(relType)
    
    
    #
    # I separate the working for ee file and et file 'cause I would expect
    # a lots of different between those two file after some more features are extracted
    ee_file = open(ee_file_name, 'r')
    ee_file_adjacent = open(ee_file_name_adjacent, 'w')
    current_line = ''
    
    for line in ee_file:
        if line[:7] != UNKNOWN_RELTYPE:
            current_line += line.split('\n')[0].strip() + ' '
        else:
            #process the previous line here
            features = current_line.split(' ')
            event_pair = ['','']
            for feature in features:
                feature = feature.strip()
                if feature[1:5] == 'eiid':
                    parts = feature.split('-')
                    if len(parts) > 1 and parts[1][:2] == 'ei':
                        event_pair[int(feature[0])] = parts[1]
            if event_pair != ['', '']:
                match_pair_with_dict_print_to_file(current_line, event_pair, ee_dict, ee_file_adjacent)
            #make a new line here
            current_line = line
    ee_file_adjacent.close()    
    
    et_file = open(et_file_name, 'r')
    et_file_adjacent = open(et_file_name_adjacent, 'w')
    current_line = ''
    
    for line in et_file:
        if line[:7] != UNKNOWN_RELTYPE:
            current_line += line.split('\n')[0].strip()
        else:
            #
            #process the previous line here
            features = current_line.split(' ')
            event_pair = ['','']
            for feature in features:
                feature = feature.strip()
                if feature[1:5] == 'eiid':
                    parts = feature.split('-')
                    if len(parts) > 1 and parts[1][:2] == 'ei':
                        event_pair[int(feature[0])] = parts[1]
                if feature[1:4] == 'tid':
                    parts = feature.split('-')
                    if len(parts) > 1 and parts[1][:1] == 't':
                        event_pair[int(feature[0])] = parts[1]
            if event_pair != ['', '']:
                match_pair_with_dict_print_to_file(current_line, event_pair, et_dict, et_file_adjacent)
                    
            #make a new line here
            current_line = line
    et_file_adjacent.close()


def switch_line (line):
    inline_features = line.split(' ')
    # For convenience and consistency
    new_line = 'UNKNOWN '
    rearrange_features = []
    rearrange_features.append([])
    rearrange_features.append([])
    rearrange_features.append([])
    
    for feature in inline_features:
        if len(feature) ==  0:
            continue
        if feature[0] == '0':
            rearrange_features[1].append('1'+feature[1:])
        elif feature[0] == '1':
            rearrange_features[0].append('0'+feature[1:])
        else:
            rearrange_features[2].append(feature)
    new_line += (' '.join([' '.join(rearrange_features[0]),
                 ' '.join(rearrange_features[1]), 
                 ' '.join(rearrange_features[1])]));
    return new_line

def match_pair_with_dict_print_to_file(line, pair, dict, file):
    # checking pair in the right order
    key = ' '.join(pair)
    if key in dict:
        relType = dict[key]
        #
        # right order, keep the initial order
        line = relType + line[7:]
        line = line.strip()
        file.write(line + '\n')
        return
    
    # checking pair in the reversed order
    # however, if pairs in the dicts
    # are in correct order, it would never come to
    # this point
    pair.reverse()
    key = ' '.join(pair)
    if key in dict:
        print 'It would never happen'
        relType = dict[key]
        #
        # reversed order, need to switch features of the first and second 
        line = relType + switch_line(line)[7:]
        line = line.strip()
        file.write(line + '\n')
        return
    
    line = NO_RELATION + line[7:]
    line = line.strip()
    file.write(line + '\n')
