from docmodel import xml_parser
from docmodel.xml_parser import Parser
from docmodel.xml_parser import XmlDocElement, XmlDocument
from utilities import logger

def merger(infile1, infile2, outfile):
    """
    Merge two files together
    - infile1: String 
    File name for the preprocessed file (with token tags)
    - infile2: String
    File name for the original file (including TIMEX3, MAKEINSTANCE, LINK)
    - outfile: String
    File name for the output file 
    """
    
    doc1 = Parser().parse_file(open(infile1, "r"))
    doc2 = Parser().parse_file(open(infile2, "r"))
    doc3 = XmlDocument();
    
#     _mark_lex_tags(doc1)
    _merge_tags(doc1, doc2, doc3)
    
    doc3.save_to_file(outfile)

def _merge_tags(doc1, doc2, doc3):
    """Add a unique id to each lex tag."""
    
    # state = None normal output
    
    original_text = []
    make_instance_dict = {}
    inside_text = False;
    
    state = None;
    
    for element in doc2:
        if inside_text:
            if  element.tag == 'EVENT' or element.tag == 'TIMEX3' or element.tag == 'SIGNAL':
                if element.is_opening_tag():
                    state = element
                elif  element.is_closing_tag():
                    state = None
            
            if not element.is_tag() and not element.is_space():
                original_text.append((element.content.strip(), state))
        if element.is_opening_tag() and element.tag == 'TEXT':
            inside_text = True
        if element.is_closing_tag() and element.tag == 'TEXT':
            inside_text = False
        if element.is_opening_tag() and element.tag == 'MAKEINSTANCE':
            make_instance_dict[element.attrs['eventID']] = element
    
    original_text_pointer = 0
    #     lex_id = 0
    if len(original_text) == 0:
        return
    
    tempo_string = original_text[original_text_pointer][0]
    state = original_text[original_text_pointer][1]
    timex_flag = 0
    signal_flag = 0
    chunk_cross_border_flag = 0
    sent_cross_border_flag = 0
    last_opening_phrase = None
    
    inside_text = False
    current_event_id = None
    
    
            
    for element in doc1:
        if element.is_opening_tag() and element.tag == 'TimeML':
            # <TimeML xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            # xsi:noNamespaceSchemaLocation="../../dtd/timeml_1.2.1.xsd">
            element = XmlDocElement('<TimeML xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\
                    xsi:noNamespaceSchemaLocation="../../dtd/timeml_1.2.1.xsd">','TimeML',
                    {'xsi:noNamespaceSchemaLocation':"../../dtd/timeml_1.2.1.xsd",
                     'xmlns': "../../dtd/timeml_1.2.1.xsd"})
        if inside_text:
            # At the beginning, if we already find a TIMEX3 or SIGNAL,
            # We have to insert s and that state tag
            if (beginning_text and element.tag == 's' and state != None 
                and (state.tag == 'TIMEX3' or state.tag == 'SIGNAL')):
                    doc3._add_doc_element_with_check(element)
                    if state.tag == 'TIMEX3':
                        timex_flag = 2
                    if state.tag == 'SIGNAL':
                        signal_flag = 2
                    doc3._add_doc_element_with_check(state)
            if beginning_text:
                beginning_text = False
            #
            # If outside of EVENT, TIMEX3 and SIGNAL
            # last_opening_phrase keep track of last opening NP or VP tag (not yet closed)
            # else == None 
            
            if ((state == None or tempo_string.strip() == '') 
                and (element.tag == 'VG' or element.tag == 'NG')):
                if element.is_opening_tag():
                    last_opening_phrase = element.tag
                else:
                    last_opening_phrase = None
                        
            if element.is_opening_tag() and element.tag == 'lex':
#                 print 'Tempo string ' + tempo_string
#                 print 'Match ' + element.next.content
                
                l_index = tempo_string.find(element.next.content)
                at_beginning = tempo_string.strip().startswith(element.next.content)
                timex_flag = 0
                signal_flag = 0
                
                # There is a problem here, when I delay the update of
                # state to the next lex
#                 if l_index == -1:
#                 if l_index == -1:
                if not at_beginning:
                    if tempo_string.strip() == '':
                        original_text_pointer += 1
                        if original_text_pointer >= len(original_text):
                            inside_text = False
                            continue
                        tempo_string = original_text[original_text_pointer][0]
                        state = original_text[original_text_pointer][1]
                        
                        # Have to recheck the last opening phrase here, after getting the new state
                        if state == None and last_opening_phrase != None:
                            last_opening_phrase = None
                        
                        # Begin a timex3
                        if state != None and state.tag == 'TIMEX3':
                            timex_flag = 1
                        # Begin a signal
                        if state != None and state.tag == 'SIGNAL':
                            signal_flag = 1
                        l_index = tempo_string.find(element.next.content)
                        if l_index == -1:
                            logger.error('String in original file %s' % tempo_string)
                            logger.error('String in preprocessed file %s' % element.next.content)
                            logger.error("Couldn't match")
                            raise Exception("Couldn't match")
                    else:
                        continue
                if state != None and state.tag == 'EVENT':
                    current_event_id = state.attrs['eid']
                    # Add event under lex tag
                    doc3._add_doc_element_with_check(element)
                    doc3._add_doc_element_with_check(state)
                if state != None and state.tag == 'TIMEX3':
                    # Add timex3 before the lex tag
                    if timex_flag == 1:
                        doc3._add_doc_element_with_check(state)
                    doc3._add_doc_element_with_check(element)
                if state != None and state.tag == 'SIGNAL':
                    # Add signal before the lex tag
                    if signal_flag == 1:
                        doc3._add_doc_element_with_check(state)
                    doc3._add_doc_element_with_check(element)
                if state == None:
                    doc3._add_doc_element_with_check(element)
                    
                tempo_string = tempo_string[l_index + len(element.next.content):]
            elif element.is_closing_tag() and element.tag == 'lex':
                #  
                # Change the flags when the tag is empty
                if state != None and state.tag == 'TIMEX3' and tempo_string.strip() == "":
                    timex_flag = 2
                if state != None and state.tag == 'SIGNAL' and tempo_string.strip() == "":
                    signal_flag = 2
                #  
                # Adding closing tags
                if state != None and state.tag == 'EVENT':
                    doc3._add_doc_element_with_check(XmlDocElement("</EVENT>", 'EVENT'))
                    doc3._add_doc_element_with_check(element)
                    try:
                        doc3._add_doc_element_with_check(make_instance_dict[current_event_id])
                        doc3._add_doc_element_with_check(XmlDocElement("</MAKEINSTANCE>", 'MAKEINSTANCE'))
                    except Exception:
                        print "EVENT doesn't has any INSTANCE" + str(current_event_id)
                if state != None and state.tag == 'TIMEX3':
                    doc3._add_doc_element_with_check(element)
                    if timex_flag == 2:
                        doc3._add_doc_element_with_check(XmlDocElement("</TIMEX3>", 'TIMEX3'))
                        if last_opening_phrase != None:
                            doc3._add_doc_element_with_check(XmlDocElement("</" + last_opening_phrase + ">",
                                                                           last_opening_phrase))
                            last_opening_phrase = None
                if state != None and state.tag == 'SIGNAL':
                    doc3._add_doc_element_with_check(element)
                    if signal_flag == 2:
                        doc3._add_doc_element_with_check(XmlDocElement("</SIGNAL>", 'SIGNAL'))
                        if last_opening_phrase != None:
                            doc3._add_doc_element_with_check(XmlDocElement("</" + last_opening_phrase + ">",
                                                                           last_opening_phrase))
                            last_opening_phrase = None
                if state == None:
                    doc3._add_doc_element_with_check(element)
                
                # new implementation
                # update the state at the last lex, not the first lex of 
                # next chunk of text
#                 if tempo_string.strip() == '':
#                     if ( original_text_pointer + 1 < len(original_text)
#                           and original_text[original_text_pointer+1][1] == None):
#                         state = None
            elif ((element.tag == 'VG' or element.tag == 'NG')
                  and state != None and (state.tag == 'TIMEX3' or state.tag == 'SIGNAL')):
                #
                # Track the existence of cross border TIMEX3, SIGNAL and VP, NP
                # If VP or NP tag is inside TIMEX3 or SIGNAL, we shouldn't add that VP or NP tags
                # We care about the last opening tag of VP or NP inside TIMEX3 and SIGNAL
                # We need to remove the corresponding closing tag later 
                # outside of TIMEX3 and SIGNAL
                if element.is_closing_tag():
                    chunk_cross_border_flag = 0
                if element.is_opening_tag():
                    chunk_cross_border_flag = state.tag
            elif (element.tag == 's' and state != None 
                  and (state.tag == 'TIMEX3' or state.tag == 'SIGNAL')):
                if element.is_closing_tag():
                    sent_cross_border_flag = 0
                if element.is_opening_tag():
                    sent_cross_border_flag = state.tag
                logger.warn('Ignore s tag 1')
            elif ((element.tag == 'VG' or element.tag == 'NG' )
                  and element.is_closing_tag()
                  and chunk_cross_border_flag != 0):
                # 
                # Find a closing tag outside of TIMEX3 or SIGNAL that corresponding to a
                # deleted opening tag inside TIMEX3 or SIGNAL
                chunk_cross_border_flag = 0
            elif (element.tag == 's'
                  and element.is_closing_tag()
                  and chunk_cross_border_flag != 0):
                sent_cross_border_flag = 0
                logger.warn('Ignore s tag 2')
            else:
                doc3._add_doc_element_with_check(element)
        else:
            if element.tag == 'MAKEINSTANCE':
                continue
            if element.previous != None and element.previous.tag == 'MAKEINSTANCE' and element.previous.is_closing_tag():
                continue
            doc3._add_doc_element_with_check(element)
        if element.is_opening_tag() and element.tag == 'TEXT':
            inside_text = True
            beginning_text = True
        if element.is_closing_tag() and element.tag == 'TEXT':
            inside_text = False
            
# merger('data/tmp/ABC19980108.1830.0711.tml.pre.xml',
#        'data/in/timebank_1.2/data/timeml/ABC19980108.1830.0711.tml',
#        'testfile.xml')
