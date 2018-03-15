from library.timeMLspec import EVENT, INSTANCE, TIMEX, EID, EVENTID
from docmodel.xml_parser import XmlSentence
from nltk.corpus import wordnet as wn
from nltk.stem.snowball import EnglishStemmer
from utilities.parsed_term import *
import re

from library.classifier.classifySpec import EE_FLAG_MAIN_INTRA_SENT, \
                                            EE_FLAG_MAIN_INTER_SENT, \
                                            EE_FLAG_CONSE_SENT, \
                                            ET_FLAG_CONSE_SENT, \
                                            ET_FLAG_WITH_DCT

"""
This vector file is a refined version of vectors.py 
which include some new more features, including the features
in current vectors, and add syntactical
tree connecting two entities, distance between two entities.
One important addition is the distinction between 
different kind of event-event pairs and event-time pairs.
Event - event pair:
    - Need to fix which event - event pairs should be included
    - Then to classify them into either BEFORE or AFTER
    - Main event - Other event in the same sentence:
        - Tree path between two events.
        - Features in vectors.
        - Tree distance between two events.
        - Sentence distance between two events.
    - Main event in consecutive sentences:
        - Hard, pass
Event - time pair:
    - Cause most of the label for this kind is INCLUDED and IS_INCLUDED, it could be made into a binary classifier for INCLUDED/ NO LABEL.
    - Two types:
        - Event - closest time entities:
            - Tree path btw two entities
            - Old Features in vectors.
            - Tree distance between event and time.
            - Sentence distance between event and time.
        - Main event - document creation time
            - Follow Bethard

"""


# these should be defined in a library for classifier features
C_TID = 'tid'
C_TYPE = 'type'
C_VALUE = 'value'
C_FUNINDOC = 'functionInDoc'
C_TEMPFUN = 'temporalFunction'
C_EID = 'eid'
C_EIID = 'eiid'
C_STRING = 'string'
C_MORPHY_STRING = 'morphy_str'
C_STEM_STRING = 'stem_str'
C_CLASS = 'Actualclass'
C_TENSE = 'tense'
C_ASPECT = 'aspect'
C_MOD = 'modality'
C_POL = 'negation'
C_TOE = 'timeorevent'
C_SHIFT_TENSE = 'shiftTen'
C_SHIFT_ASPECT = 'shiftAspect'
C_SIGNAL = 'Signal'
C_TOKEN_BETWEEN = 'tokenBetween'
C_POS_IN_BETWEEN = 'INBetween'
C_POS_VB_BETWEEN = 'VBBetween'
C_TIME_MOD = 'time_mod'
C_DISTANCE_BTW = 'distanceBetween'
C_TREE_DISTANCE_BTW = 'treeDistanceBetween'
SVM_FEATURE = 'svm_feature'
AUXILLARY_FEATURE = 'auxillary_feature'

snowball_steammer = EnglishStemmer()

EVENT_ATTRIBUTE_MAPPINGS = {
SVM_FEATURE:
     [[C_CLASS, 'class'], [C_ASPECT, 'aspect'], 
      [C_MOD, 'modality'], [C_POL, 'polarity'],
     [C_STRING, 'string'], [C_TENSE, 'tense'], [C_TOE, 'timeorevent'],
     [C_MORPHY_STRING, 'morphy'], [C_STEM_STRING, 'stem']],
AUXILLARY_FEATURE:
    [[C_EID, 'eid'], [C_EIID, 'eiid']]
}

TIMEX_ATTRIBUTE_MAPPINGS = {
SVM_FEATURE:
     [[C_TOE, 'timeorevent'], [C_STRING, 'string'],
     [C_FUNINDOC, 'functionInDoc'], [C_TEMPFUN, 'temporalFunction'],
     [C_TYPE, 'type'], [C_TIME_MOD, 'mod']],
AUXILLARY_FEATURE:
    [[C_TID, 'tid']]
}


VECTOR_CLASS = 'Vector class'
FEATURE_FILE = 'Feature file'

BEGIN_TREE_TAG = ' |BT| '
END_TREE_TAG = ' |ET| '
BEGIN_VECTOR_TAG = ' |BV| '
END_VECTOR_TAG = ' |EV| '
 
def create_vectors(xmldoc, parsed_doc, feature_index_dict, ee_file, et_file):
    """Create vector based on the different relation."""

    # collect the instance so we can merge in the information when we
    # find and event.    
    instances = {}
    for instance in xmldoc.get_tags(INSTANCE):
        eid = instance.attrs.get(EVENTID, None)
        instances[eid] = instance
    
    ee_file = open(ee_file, 'w') 
    et_file = open(et_file, 'w')
    
    file_map = {EE_FLAG_MAIN_INTRA_SENT: 
                {VECTOR_CLASS: EEVector, FEATURE_FILE: ee_file},
                EE_FLAG_MAIN_INTER_SENT: 
                {VECTOR_CLASS: EEVector, FEATURE_FILE:ee_file},
                EE_FLAG_CONSE_SENT: 
                {VECTOR_CLASS: EEVector, FEATURE_FILE:ee_file},
                ET_FLAG_CONSE_SENT: 
                {VECTOR_CLASS: ETVector, FEATURE_FILE:et_file},
                ET_FLAG_WITH_DCT: 
                {VECTOR_CLASS: ETVector, FEATURE_FILE:et_file}
                }
    
    def write_feature( vector_1, vector_2, flag ):
        file_to_write = file_map[flag][FEATURE_FILE]
        vector_class = file_map[flag][VECTOR_CLASS]
        file_to_write.write(vector_class(vector_1, vector_2, 
                    flag).as_string(feature_index_dict) + "\n")
    
    doc_sentences = xmldoc.get_sentences()
    main_event_list = []
    for sent_index in xrange(len(doc_sentences)):
        sentence = doc_sentences[sent_index]
        sentence_tree = parsed_doc[sent_index].tree
         
        """
        ============================================================
        Check main event with another event in the same sentence
        ============================================================
        """
        event_pos = []
        event_list = sentence.get_events()
        for event, extend in event_list:
            # Extend in event is count from 1 
            # while extend in tree count from 0
            # So need to reduce 1
            event_pos.append(extend[0] - 1)
        
        main_event_index = sentence_tree.get_highest_event(event_pos)
        if main_event_index == None:
            continue
        main_event, main_extend = event_list[main_event_index]
        
        main_eid = main_event.attrs.get(EID, None)
        if main_eid in instances:
            main_event_vector = EventVector(main_event, main_extend, 
                                            sentence, sentence_tree, instances[main_eid])
            main_event_list.append(main_event_vector)
          
            for i in xrange(len(event_list)):
                """
                Outdated, if don't need to has consecutive event TLINK,
                don't need to check this one
                """
#                 if i != main_event_index and i != main_event_index - 1 and i != main_event_index + 1:
                if i != main_event_index:
                    event, extend = event_list[i]
                    eid = event.attrs.get(EID, None)
                    if eid in instances:
                        event_vector = EventVector(event, extend, sentence,
                                                    sentence_tree, instances[eid])
                        if i < main_event_index:
                            write_feature(event_vector, main_event_vector,
                                          EE_FLAG_MAIN_INTRA_SENT)
                        else:
                            write_feature(main_event_vector, event_vector, 
                                          EE_FLAG_MAIN_INTRA_SENT)
        
        """
        ============================================================
        Check consecutive events or event time in the same sentence
        ============================================================
        """
        object_vectors = []
        ets = sentence.get_times_and_events()
        for i in xrange(len(ets)):
            et, extend, flag = ets[i]
            eid = et.attrs.get(EID, None)
            if flag == XmlSentence.EVENT_FLAG:
                if eid in instances:
                    object_vectors.append(EventVector(et, extend, sentence,
                                                      sentence_tree, instances[eid]))
                else:
                    object_vectors.append(Vector())
            if flag == XmlSentence.TIMEX_FLAG:
                object_vectors.append(TimexVector(et, extend, sentence, sentence_tree))
          
          
        for i in range(0, len(ets) - 1):
            v1 = object_vectors[i]
            v2 = object_vectors[i + 1]
            
            
            if v1.is_event_vector() and v2.is_event_vector():
                """
                Turn off consecutive event in the same sentence
                """  
                pass
#                 write_feature(v1, v2, EE_FLAG_CONSE_SENT)
            elif v1.is_event_vector() and v2.is_timex_vector():
                write_feature(v1, v2, ET_FLAG_CONSE_SENT)
            elif v1.is_timex_vector() and v2.is_event_vector():
                write_feature(v1, v2, ET_FLAG_CONSE_SENT)
    """
    ============================================================
    Check main events in consecutive sentences
    ============================================================
    """
    for i in range(len(main_event_list) - 1):
        v1 = main_event_list[i]
        v2 = main_event_list[i + 1]
        write_feature(v1, v2, EE_FLAG_MAIN_INTER_SENT)
      
    """
    ============================================================
    Check main events and the document creation time
    ============================================================
    """
    dct_vector = TimexVector(xmldoc.get_dct(), None, None, None)
    for i in range(len(main_event_list)):
        v = main_event_list[i]
        write_feature(dct_vector, v, ET_FLAG_WITH_DCT)


            
class Vector:
    def is_event_vector(self):
        return False

    def is_timex_vector(self):
        return False

    def as_string(self, i, feature_index_dict):
        """
        Turn the vector into a string of feature in the following form:
            - feature_index:value feature_index:value
            Example:
            0:1 10:1 20:1
            Feature are NOT YET ordered by index
            Parameter:
                i: Whether the vector is the first or second entity in the pair
        """
        x = []
        for feature_type in self.mappings:
            for (name, attr) in self.mappings[feature_type]:
                attrs = self.get_value(attr)
                if type(attrs) == list:
                    for att in attrs:
                        feature_name = "%d%s-%s" % (i, name, att)
                        if feature_type == SVM_FEATURE:
                            feature_index = feature_index_dict.get_index(feature_name)
                            x.append("%d:%d" % (feature_index, 1))
                        elif feature_type == AUXILLARY_FEATURE:
                            x.append(feature_name)
                else:
                    feature_name = "%d%s-%s" % (i, name, attrs)
                    if feature_type == SVM_FEATURE:
                        feature_index = feature_index_dict.get_index(feature_name)
                        x.append("%d:%d" % (feature_index, 1))
                    elif feature_type == AUXILLARY_FEATURE:
                        x.append(feature_name)
        
        return ' '.join(x)
    
    def get_feature_values(self, i, feature_index_dict):
        """
        Turn the vector into a list of features and values:
            - [(feature_index,value),(feature_index,value)]
            Example:
            [(0,1),(10,1),(20,1)]
            Feature are NOT YET ordered by index
            Parameter:
                i: Whether the vector is the first or second entity in the pair
        
        Assuming that the feature for each entity (event and time) are text, not numeric value
        """
        feature_values = []
        for feature_type in self.mappings:
            for (name, attr) in self.mappings[feature_type]:
                attrs = self.get_value(attr)
                if type(attrs) == list:
                    for att in attrs:
                        feature_name = "%d%s-%s" % (i, name, att)
                        if feature_type == SVM_FEATURE:
                            feature_index = feature_index_dict.get_index(feature_name)
                            feature_values.append((feature_index, 1))
                        elif feature_type == AUXILLARY_FEATURE:
                            feature_values.append((feature_name, 'None value'))
                else:
                    feature_name = "%d%s-%s" % (i, name, attrs)
                    if feature_type == SVM_FEATURE:
                        feature_index = feature_index_dict.get_index(feature_name)
                        feature_values.append((feature_index, 1))
                    elif feature_type == AUXILLARY_FEATURE:
                        feature_values.append((feature_name, 'None value'))
        
        return feature_values


class EventVector(Vector):

    def __init__(self, event, extend, sentence, sentence_tree, instance):
        # Fix extend from last index inclusive to exclusive
        if type(extend) == tuple:
            self.extend = (extend[0] - 1, extend[1])
        else:
            self.extend = extend
        self.attrs = event.attrs
        self.attrs.update(instance.attrs)
        self.attrs['string'] = event.collect_text_content().replace(' ', '_')
        self.mappings = EVENT_ATTRIBUTE_MAPPINGS
        self.sentence = sentence
        self.sentence_tree = sentence_tree
        
    def is_event_vector(self):
        return True
    
    def get_value(self, attr):
        if attr == 'modality':
            return self.attrs.get(attr, 'NONE')
        elif attr == 'timeorevent':
            return 'event'
        elif attr == 'polarity':
            if self.attrs.get(attr, 'POS') == 'POS':
                return 'NONE'
            else:
                return 'NEG'
        elif attr == 'morphy':
#             return [wn.morphy(token) for token in self.attrs['string']]
            if type(self.attrs['string']) == list:
                return [wn.morphy(token) for token in self.attrs['string']]
#             elif type(self.attrs['string']) == str:
            t = set()
            for pos in ['v', 'n']:
                morphed_token = wn.morphy(self.attrs['string'], pos)
                if morphed_token != None:
                    t.add(morphed_token)
            return list(t)
        elif attr == 'stem':
            if type(self.attrs['string']) == list:
                return [snowball_steammer.stem(token) for token in self.attrs['string']]
            return snowball_steammer.stem(self.attrs['string'])
        return self.attrs[attr]
    
    
class TimexVector(Vector):

    def __init__(self, timex, extend, sentence, sentence_tree):
        # Fix extend from last index inclusive to exclusive
        if type(extend) == tuple:
            self.extend = (extend[0] - 1, extend[1])
        else:
            self.extend = extend
        self.attrs = timex.attrs
        timex_string = timex.collect_text_content()
        timex_tokens = timex_string.split(' ')
        self.attrs['string'] = timex_tokens
        self.mappings = TIMEX_ATTRIBUTE_MAPPINGS
        self.sentence = sentence
        self.sentence_tree = sentence_tree
        
    def is_timex_vector(self):
        return True
    
    def get_value(self, attr):
        if attr == 'temporalFunction':
            return 'time'
        if attr == 'timeorevent':
            return 'TIME'
        elif attr == 'functionInDoc':
            return self.attrs.get(attr, 'false')
        elif attr == 'temporalFunction':
            return self.attrs.get(attr, 'time')
        return self.attrs.get(attr, 'no_val')

class CombinedVector:
    """
    Vector that would be written into file. It would include the vectors
    of two involved entities, and the mutual features between them.  
    """
    
    def __init__(self, entity_vector1 , entity_vector2, flag = None):
        self.v1 = entity_vector1
        self.v2 = entity_vector2
        self._mutual_features = []
        if flag != None:
            self._mutual_features.append((flag,1))
    
    def vector_string(self, feature_index_dict):
        str = ""
        feature_values = []
        feature_values += self.v1.get_feature_values(0, feature_index_dict)
        feature_values += self.v2.get_feature_values(1, feature_index_dict)
        
        for feature_name, feature_value in self._mutual_features:
            feature_index = feature_index_dict.get_index(feature_name)
            feature_values.append((feature_index, feature_value))
            
        feature_values = sorted(set(feature_values), key=lambda fv: fv[0])
        for feature, value in feature_values:
            if type(value) == int:
                str += " %d:%d" % (int(feature), value)
            else:
                str += " %s" % feature
        return str
    
    def tree_string(self):
        if self.v1.sentence == self.v2.sentence:
            pt_sub_tree = str(self.v1.sentence_tree.parse_tree_for_sub_component(self.v1.extend[0],
                                                                      self.v1.extend[1],
                                                                      self.v2.extend[0],
                                                                      self.v2.extend[1], SUBTREE_HPPT))
            tree_string = str(pt_sub_tree)
            tree_string = re.subn('\n','',tree_string)[0]
            tree_string = re.subn(r'\s+',' ',tree_string)[0]
            return tree_string
        return ""
        
    def as_string(self, feature_index_dict):
        str = 'UNKNOWN'
        str += BEGIN_TREE_TAG
        str += self.tree_string()
        str += END_TREE_TAG 
        str += self.vector_string(feature_index_dict)
        return str
        
# class TTVector(CombinedVector):
#     """Class responsible for creating the vector between two timex3. Uses
#     the vectors of each timex.
#     """
#     def __init__(self, timex_vector1, timex_vector2):
#         CombinedVector.__init__(self, timex_vector1, timex_vector2)

class EEVector(CombinedVector):

    """Class responsible for creating the vector between two events. Uses
    the vectors of each event and creates three extra features:
    Signal, shiftAspect and shiftTen. The result looks like:

        UNKNOWN 0eid=e1 0Actualclass-OCCURRENCE 0aspect-NONE
        0modality-NONE # 0negation-NONE 0string-exploded 0te\nse-PAST
        0timeorevent-event # 0eid-e2 1Actualclass-OCCURRENCE
        1aspect-NONE 1modality-NONE # 1negation-NONE \1string-killing
        1tense-NONE 1timeorevent-event # Signal-NONE shiftAspect-0
        shiftTen-1
    
    Adding some extra features here, following Steven Berthard's paper:
        The text of the first child of the grandparent of the
        event in the constituency tree, for each event (not sure what's that for)
        The path through the syntactic constituency tree
        from one event to the other (later)
        The tokens appearing between the two events (now)
    """
    
    def __init__(self, event_vector1, event_vector2, flag = None):
        CombinedVector.__init__(self, event_vector1, event_vector2, flag)
        self.shiftAspect = 1
        self.shiftTen = 1
        if self.v1.get_value('tense') == self.v2.get_value('tense'):
            self.shiftTen = 0
        if self.v1.get_value('aspect') == self.v2.get_value('aspect'):
            self.shiftAspect = 0
            
        self._mutual_features += [(C_SHIFT_ASPECT, self.shiftAspect),
                                (C_SHIFT_TENSE, self.shiftTen)]
        
        # Sentence level features
        if (self.v1.sentence == self.v2.sentence):
            self.sentence = self.v1.sentence
            
            self._mutual_features.append((C_DISTANCE_BTW, self.v2.extend[0] - self.v1.extend[1]))
             
            tree_distance = self.v1.sentence_tree.\
                get_tree_distance(self.v1.extend[0],
                                  self.v1.extend[1],
                                  self.v2.extend[0],
                                  self.v2.extend[1])
             
            self._mutual_features.append((C_TREE_DISTANCE_BTW, tree_distance))
            if (flag == EE_FLAG_MAIN_INTRA_SENT):
                pass
            elif (flag == EE_FLAG_CONSE_SENT):
                # Get all tokens in between two events
                between_tokens = self.sentence.get_tokens( (self.v1.extend[1] + 1, self.v2.extend[0] - 1 ))
                for token in between_tokens:
                    self._mutual_features.append(("%s-%s" % (C_TOKEN_BETWEEN, token), 1))
        elif (flag == EE_FLAG_MAIN_INTER_SENT):
            pass

class ETVector(CombinedVector):

    """Class responsible for creating the vector between an event and a
    time. Uses the event and time vectors and adds one extra feature:
    Signal. The result looks like:

        UNKNOWN 0Actualclass-OCCURRENCE 0aspect-NONE 0modality-NONE
        0negation-NONE 0string-killed 0tense-PAST 0timeorevent-event#
        1timeorevent-NONE 1string-Friday 1functionInDoc-false
        1temporalFunction-time 1type-DATE 1value-1998-08-07 Signal-NONE"""

    def __init__(self, vector1, vector2, flag = None):
        CombinedVector.__init__(self, vector1, vector2, flag)
        
        # Sentence level features
        if (self.v1.sentence == self.v2.sentence):
            self.sentence = self.v1.sentence
            
            self._mutual_features.append((C_DISTANCE_BTW, self.v2.extend[0] - self.v1.extend[1]))
            
            tree_distance = self.v1.sentence_tree.\
                get_tree_distance(self.v1.extend[0],
                                  self.v1.extend[1],
                                  self.v2.extend[0],
                                  self.v2.extend[1])
            
            self._mutual_features.append((C_TREE_DISTANCE_BTW, tree_distance))
            
            """
            Actually this check is not necessary, but just to make it clearer
            """
            if flag == ET_FLAG_CONSE_SENT:
                # Get all tokens between two events which has POS = 'IN'
                in_between_tokens = self.sentence.get_tokens((self.v1.extend[1] + 1,
                                                              self.v2.extend[0] - 1),
                                                            lambda lex: lex.attrs['pos'] == 'IN')
                 
                for token in in_between_tokens:
                    self._mutual_features.append(("%s-%s" % (C_POS_IN_BETWEEN, token), 1))
                # Get all tokens between two events which has POS = 'VB*'
                verb_between_tokens = self.sentence.get_tokens((self.v1.extend[1] + 1,
                                                              self.v2.extend[0] - 1),
                                                              lambda lex: lex.attrs['pos'][:2] == 'VB')
                
                for token in verb_between_tokens:
                    self._mutual_features.append(("%s-%s" % (C_POS_VB_BETWEEN, token), 1))