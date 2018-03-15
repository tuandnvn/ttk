import os
import re
import sqlite3
from library.tlink_relation import BEFORE, AFTER, SIMULTANEOUS

DIR_LEXICAL_RULES = os.path.join('library','classifier','lexical_rules')
DATABASE_FILE = 'ordering.lemmas.closed.nones0.5.stats'

class ClassifierRuleDictionary:
    """
    This class is to store the lexical rules 
    Save and load the lexical rule text file into database
    There would be some component to turn the order database into a prior
    Currently, the only module is to count the number of pairs of events 
    in an input file (with extracted events) that could be found in the database.
    
    The raw estimation of the order between two verb could be used 
    as a feature if it's certain enough.
    For example, if verb event A come before verb event B 80% of the time
    in the database, we could use Database-BEFORE as a feature
    """
    def __init__(self):
        self.database_text_file = os.path.join( DIR_LEXICAL_RULES, DATABASE_FILE)
        self.database_file = os.path.join( DIR_LEXICAL_RULES, DATABASE_FILE + '.db')
        self._conn = None
    
    @classmethod
    def get_single_instance(cls):
        try:
            return cls.crd
        except Exception:
            cls.crd = ClassifierRuleDictionary()
            cls.crd.read_lexical_rules_into_dict()
            return cls.crd
        
    def read_lexical_rules_into_database (self):
        f = open(self.database_text_file,'r')
        c = self.open_connection().cursor()
        
        # Create table
        try:
            c.execute('''CREATE TABLE orders
             (verb1 text, verb2 text, freq1 int, freq2 int)''')
        except sqlite3.OperationalError:
            print 'TABLE orders already exists'
        
        frequency_dict = {}
        for line in f:
            first_verb, second_verb, frequency = line.strip().split('\t')
            
            if ( second_verb + ' ' + first_verb in frequency_dict): 
                frequency_dict[second_verb + ' ' + first_verb][1] = int(frequency)
            else:
                frequency_dict[first_verb + ' ' + second_verb] = [int(frequency),0]
        
        prepared_data = []
        for key in frequency_dict:
            freq1, freq2 = frequency_dict[key]
            first_verb, second_verb = key.split(' ')
            prepared_data.append((first_verb, second_verb, freq1, freq2))
        c.executemany('INSERT INTO orders VALUES (?,?,?,?)', prepared_data)
        self.close_connection()
        print '=============Done creating database==========='
    
    def read_lexical_rules_into_dict (self):
        f = open(self.database_text_file,'r')
        self.lexical_rule_dict = {}
        self.total_of_freq = 0
        for line in f:
            first_verb, second_verb, frequency = line.strip().split('\t')
            self.total_of_freq += int(frequency)
            
            if (second_verb , first_verb) in self.lexical_rule_dict: 
                self.lexical_rule_dict[(second_verb , first_verb)][1] = int(frequency)
            else:
                self.lexical_rule_dict[(first_verb , second_verb)] = [int(frequency),0]
        self.no_of_pairs = len(self.lexical_rule_dict.keys())
    
    def get_lemma_pair_prob(self, lemma_pair, label):
        """
        Calculate P ( lemma_pair | label ) with label = [BEFORE, AFTER, *SIMULTANEOUS]
        Could be calculated directly by the number of pairs in the 
        narrative scheme, or by doing a smoothing step.
        P ( lemma_pair | SIMULTANEOUS ) is set == 1/2N where N is the total 
        number of pair line in the corpus. (2 because lemma pair could be
        swapped).
        """
        if label == SIMULTANEOUS:
            no_of_instance = 0
            
            """
            Eighth try
            For SIMULTENEOUS, the result needs to reflect
            the distribution of lemma_pair
            """
            if lemma_pair in self.lexical_rule_dict:
                 no_of_instance = (self.lexical_rule_dict[lemma_pair][0] +
                                   self.lexical_rule_dict[lemma_pair][1])
                 return float(no_of_instance)/(2*self.total_of_freq)
            elif (lemma_pair[1], lemma_pair[0]) in self.lexical_rule_dict:
                 no_of_instance = (self.lexical_rule_dict[(lemma_pair[1], lemma_pair[0])][0] +
                                   self.lexical_rule_dict[(lemma_pair[1], lemma_pair[0])][1])
                 return float(no_of_instance)/(2*self.total_of_freq)
#             if (lemma_pair in self.lexical_rule_dict 
#                 or (lemma_pair[1], lemma_pair[0]) in self.lexical_rule_dict):
#                 return float(1)/(2*self.no_of_pairs)
            else:
                """
                Need to do some smoothing here
                """
                return 0
        """
        Because P ( (v1, v2) | BEFORE ) == P( (v2,v1) | AFTER ),
        we just need to calculate one relation.
        AFTER is switched to BEFORE
        """
        if label == AFTER:
            lemma_pair = (lemma_pair[1], lemma_pair[0])
        
        if lemma_pair in self.lexical_rule_dict: 
            number_of_before = self.lexical_rule_dict[lemma_pair][0]
            """
            Need to do some smoothing here
            """
            return float(number_of_before)/self.total_of_freq
        elif (lemma_pair[1], lemma_pair[0]) in self.lexical_rule_dict:
            number_of_before = self.lexical_rule_dict[(lemma_pair[1], lemma_pair[0])][1]
            """
            Need to do some smoothing here
            """
            return float(number_of_before)/self.total_of_freq
        else:
            """
            Need to do some smoothing here
            """
            return 0
    
    def get_lemma_pair_prob_smoothing(self, lemma_pair, label):
        """
        Calculate P ( lemma_pair | label ) with label = [BEFORE, AFTER, *SIMULTANEOUS]
        Could be calculated directly by the number of pairs in the 
        narrative scheme, or by doing a smoothing step.
        P ( lemma_pair | SIMULTANEOUS ) is set == 1/2N where N is the total 
        number of pair line in the corpus. (2 because lemma pair could be
        swapped).
        """
        if label == SIMULTANEOUS:
            no_of_instance = 0
            
            """
            Eighth try
            For SIMULTENEOUS, the result needs to reflect
            the distribution of lemma_pair
            """
            if lemma_pair in self.lexical_rule_dict:
                 no_of_instance = (self.lexical_rule_dict[lemma_pair][0] +
                                   self.lexical_rule_dict[lemma_pair][1])
                 return float(no_of_instance)/(2*self.total_of_freq)
            elif (lemma_pair[1], lemma_pair[0]) in self.lexical_rule_dict:
                 no_of_instance = (self.lexical_rule_dict[(lemma_pair[1], lemma_pair[0])][0] +
                                   self.lexical_rule_dict[(lemma_pair[1], lemma_pair[0])][1])
                 return float(no_of_instance)/(2*self.total_of_freq)
#             if (lemma_pair in self.lexical_rule_dict 
#                 or (lemma_pair[1], lemma_pair[0]) in self.lexical_rule_dict):
#                 return float(1)/(2*self.no_of_pairs)
            else:
                """
                Need to do some smoothing here
                """
                return 0
        """
        Because P ( (v1, v2) | BEFORE ) == P( (v2,v1) | AFTER ),
        we just need to calculate one relation.
        AFTER is switched to BEFORE
        """
        if label == AFTER:
            lemma_pair = (lemma_pair[1], lemma_pair[0])
        
        if lemma_pair in self.lexical_rule_dict: 
            number_of_before = self.lexical_rule_dict[lemma_pair][0]
            number_of_after = self.lexical_rule_dict[lemma_pair][1]
            """
            Need to do some smoothing here
            """
            return float(3*number_of_before + number_of_after)/(4*self.total_of_freq)
        elif (lemma_pair[1], lemma_pair[0]) in self.lexical_rule_dict:
            number_of_before = self.lexical_rule_dict[(lemma_pair[1], lemma_pair[0])][1]
            number_of_after = self.lexical_rule_dict[(lemma_pair[1], lemma_pair[0])][0]
            """
            Need to do some smoothing here
            """
            return float(3*number_of_before + number_of_after)/(4*self.total_of_freq)
        else:
            """
            Need to do some smoothing here
            """
            return 0
            

    def open_connection(self):
#         print self.database_file
        self._conn = sqlite3.connect(self.database_file)
        return self._conn
    
    def close_connection(self):
        self._conn.commit()
        self._conn.close()
        
    def check_in_database(self, verb_event1, verb_event2):
        if self._conn == None:
            self.open_connection()
        c = self._conn.cursor()
        c.execute('SELECT * FROM orders WHERE verb1=? AND verb2=?', (verb_event1, verb_event2))
        rows1 = c.fetchall()
        c.execute('SELECT * FROM orders WHERE verb1=? AND verb2=?', (verb_event2, verb_event1))
        rows2 = c.fetchall()
        
        if len(rows1) == 1 and len(rows2) == 1:
            raise Exception('Database has duplicate.')
        if len(rows1) == 1:
            return ( rows1[0][2], rows1[0][3] )
        if len(rows2) == 1:
            return ( rows2[0][3], rows2[0][2] )
        return None
    
    def check_in_dict(self, verb_event1, verb_event2):
        if (verb_event1, verb_event2) in self.lexical_rule_dict:
            return self.lexical_rule_dict[(verb_event1, verb_event2)]
        if (verb_event2, verb_event1) in self.lexical_rule_dict:
            return [self.lexical_rule_dict[(verb_event2, verb_event1)][1],
                    self.lexical_rule_dict[(verb_event2, verb_event1)][0]]
        return [0,0]

# crd = ClassifierRuleDictionary()
# # return    audition    3
# # anger    deny    5
# print crd.check_in_database('audition', 'return')
# print crd.check_in_database('anger', 'deny')
