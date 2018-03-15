
from library.timeMLspec import EVENT, INSTANCE, TIMEX, EID, EVENTID
from docmodel.xml_parser import XmlSentence
from nltk.corpus import wordnet as wn
from nltk.stem.snowball import EnglishStemmer

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
snowball_steammer = EnglishStemmer()

EVENT_ATTRIBUTE_MAPPINGS = \
    [[C_EID, 'eid'], [C_EIID, 'eiid'], [C_CLASS, 'class'],
     [C_ASPECT, 'aspect'], [C_MOD, 'modality'], [C_POL, 'polarity'],
     [C_STRING, 'string'], [C_TENSE, 'tense'], [C_TOE, 'timeorevent'],
     [C_MORPHY_STRING, 'morphy'], [C_STEM_STRING, 'stem']]

TIMEX_ATTRIBUTE_MAPPINGS = \
    [[C_TID, 'tid'], [C_TOE, 'timeorevent'], [C_STRING, 'string'],
     [C_FUNINDOC, 'functionInDoc'], [C_TEMPFUN, 'temporalFunction'],
     [C_TYPE, 'type'], [C_VALUE, 'value'], [C_TIME_MOD, 'mod']]


def create_vectors(xmldoc, ee_file, et_file):

    """New method that takes over the functionality of the old
    Perl script named prepareClassifier."""

    # collect the instance so we can merge in the information when we
    # find and event.    
    instances = {}
    for instance in xmldoc.get_tags(INSTANCE):
        eid = instance.attrs.get(EVENTID, None)
        instances[eid] = instance
    
    ee_file = open(ee_file, 'w') 
    et_file = open(et_file, 'w')
#     tt_file = open(tt_file, 'w') 
    # get object vectors simply by creating a list of all events and times
    # old implementation
#     object_vectors = []
#     for el in xmldoc:
#         if el.is_opening_tag():
#             if el.tag == EVENT:
#                 eid = el.attrs.get(EID, None)
#                 object_vectors.append(EventVector(el, instances[eid]))
#             if el.tag == TIMEX:
#                 object_vectors.append(TimexVector(el))
#     for i in range(0,len(object_vectors)-1):
#         v1 = object_vectors[i]
#         v2 = object_vectors[i+1]
#         if v1.is_event_vector() and v2.is_event_vector():
#             ee_file.write(EEVector(v1,v2).as_string() + "\n")
#         elif v1.is_event_vector() and v2.is_timex_vector():
#             et_file.write(ETVector(v1,v2).as_string() + "\n")
#         elif v1.is_timex_vector() and v2.is_event_vector():
#             et_file.write(ETVector(v2,v1).as_string() + "\n")

    # new implementation
    # only include pair of events or event and time in the same sentence
    
    doc_sentences = xmldoc.get_sentences()
    
    for sent_index in xrange(len(doc_sentences)):
        sentence = doc_sentences[sent_index]
        object_vectors = []
        ets = sentence.get_times_and_events()
        for i in xrange(len(ets)):
            et, extend, flag = ets[i]
            eid = et.attrs.get(EID, None)
            if flag == XmlSentence.EVENT_FLAG:
                if eid in instances:
                    object_vectors.append(EventVector(et, extend, sentence, instances[eid]))
                else:
                    object_vectors.append(Vector())
            if flag == XmlSentence.TIMEX_FLAG:
                object_vectors.append(TimexVector(et, extend, sentence))
        for i in range(0, len(ets) - 1):
            v1 = object_vectors[i]
            v2 = object_vectors[i + 1]
            
            if v1.is_event_vector() and v2.is_event_vector():
                ee_file.write(EEVector(v1, v2).as_string() + "\n")
            elif v1.is_event_vector() and v2.is_timex_vector():
                et_file.write(ETVector(v1, v2).as_string() + "\n")
            elif v1.is_timex_vector() and v2.is_event_vector():
                et_file.write(ETVector(v1, v2).as_string() + "\n")
#             elif v1.is_timex_vector() and v2.is_timex_vector():
#                 tt_file.write(TTVector(v1, v2).as_string() + "\n")
            

class Vector:
    def is_event_vector(self):
        return False

    def is_timex_vector(self):
        return False

    def as_string(self, i):
        x = []
        for (name, attr) in self.mappings:
            attrs = self.get_value(attr)
            if type(attrs) == list:
                for att in attrs:
                    x.append("%d%s-%s" % (i, name, att))
            else:
                x.append("%d%s-%s" % (i, name, attrs))
        return ' '.join(x)


class EventVector(Vector):

    def __init__(self, event, extend, sentence, instance):
        self.extend = extend
        self.attrs = event.attrs
        self.attrs.update(instance.attrs)
        self.attrs['string'] = event.collect_text_content().replace(' ', '_')
        self.mappings = EVENT_ATTRIBUTE_MAPPINGS
        self.sentence = sentence
        
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

    def __init__(self, timex, extend, sentence):
        self.extend = extend
        self.attrs = timex.attrs
        timex_string = timex.collect_text_content()
        timex_tokens = timex_string.split(' ')
        self.attrs['string'] = timex_tokens
        self.mappings = TIMEX_ATTRIBUTE_MAPPINGS
        self.sentence = sentence
        
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
    
    def __init__(self, entity_vector1 , entity_vector2):
        self.v1 = entity_vector1
        self.v2 = entity_vector2
    
    def as_string(self):
        string = 'UNKNOWN'
        string += ' %s %s' % (self.v1.as_string(0), self.v2.as_string(1))
        for feature_name, feature_values in self._mutual_features:
            for feature_value in feature_values:
                string += ' %s-%s' % (feature_name, feature_value)
        return string
        
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
    
    def __init__(self, event_vector1, event_vector2):
        CombinedVector.__init__(self, event_vector1, event_vector2)
        self.shiftAspect = 1
        self.shiftTen = 1
        if self.v1.get_value('tense') == self.v2.get_value('tense'):
            self.shiftTen = 0
        if self.v1.get_value('aspect') == self.v2.get_value('aspect'):
            self.shiftAspect = 0
            
        self._mutual_features = [(C_SIGNAL, ['NONE']),
                                (C_SHIFT_ASPECT, [str(self.shiftAspect)]),
                                (C_SHIFT_TENSE, [str(self.shiftTen)])]
        
        # Sentence level features
        if (self.v1.sentence == self.v2.sentence):
            self.sentence = self.v1.sentence
        # Get all tokens in between two events
        between_tokens = self.sentence.get_tokens( (self.v1.extend[1] + 1, self.v2.extend[0] - 1 ))
        self._mutual_features.append((C_TOKEN_BETWEEN, between_tokens))


class ETVector(CombinedVector):

    """Class responsible for creating the vector between an event and a
    time. Uses the event and time vectors and adds one extra feature:
    Signal. The result looks like:

        UNKNOWN 0Actualclass-OCCURRENCE 0aspect-NONE 0modality-NONE
        0negation-NONE 0string-killed 0tense-PAST 0timeorevent-event#
        1timeorevent-NONE 1string-Friday 1functionInDoc-false
        1temporalFunction-time 1type-DATE 1value-1998-08-07 Signal-NONE"""

    def __init__(self, vector1, vector2):
        CombinedVector.__init__(self, vector1, vector2)
        self._mutual_features = [(C_SIGNAL, ['NONE'])]
        
        # Sentence level features
        if (self.v1.sentence == self.v2.sentence):
            self.sentence = self.v1.sentence
         
         
        # Get all tokens between two events which has POS = 'IN'
        in_between_tokens = self.sentence.get_tokens((self.v1.extend[1] + 1,
                                                      self.v2.extend[0] - 1),
                                                    lambda lex: lex.attrs['pos'] == 'IN')
         
        self._mutual_features.append((C_POS_IN_BETWEEN, in_between_tokens))
        # Get all tokens between two events which has POS = 'VB*'
        verb_between_tokens = self.sentence.get_tokens((self.v1.extend[1] + 1,
                                                      self.v2.extend[0] - 1),
                                                      lambda lex: lex.attrs['pos'][:2] == 'VB')
        self._mutual_features.append((C_POS_VB_BETWEEN, verb_between_tokens))