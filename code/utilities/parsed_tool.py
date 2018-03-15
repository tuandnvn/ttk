from utilities.parsed_term import *
from parsed_tree import Tree
import re

token_map = {'-LRB-':{'content':'(',
              'pos':'('},
              '-RRB-':{'content':')',
              'pos':')'}}

"""
A combination of key used to replace space
"""
REPLACE_SPACE = '*12f1fvd9df23f32f32*'

class Parsed_Token:
    def __init__(self, parameters_array, sentence):
        self.head = None
        self.sentence = sentence
        try:
            (self.content, self.l_extend,
                self.r_extend, self.lemma,
                 self.pos, self.entity) = parameters_array
            content = self.content
            if content in token_map:
                self.content = self.lemma = token_map[content]['content']
                self.pos = token_map[content]['pos']
        except ValueError:
            print 'parameters_array has wrong number of parameters'
            return
        
#         """
#         Caution:
#             This script is to check whether the content
#             are correct, because Stanford Parser has 
#             some problem parsing fraction number.
#             However, checking the length can only ensure 
#             that the length of token is correct, not the string
#         """
#         if int(self.r_extend) - int(self.l_extend) != len(self.content):
# #             print 'There should be matching here'
# #             print self.content
# #             print len(self.content)
# #             print self.r_extend
# #             print self.l_extend
#             sentence_text = self.sentence.document.text[self.sentence.index]
#             # Get the relative position in the sentence
#             if len(self.sentence) > 0:
#                 pos_l_extend = int(self.l_extend) - int(self.sentence[0].l_extend)
#                 original_text = sentence_text[pos_l_extend: pos_l_extend
#                                                + int(self.r_extend) - int(self.l_extend)]
#             else:
#                 original_text = sentence_text[: int(self.r_extend) - int(self.l_extend)]
# #             print original_text
#             self.content = self.lemma = original_text
        """
        Caution:
            This script is to check whether the content are correct,
            because Stanford Parser sometimes change the token in
            unexpected way. 
            However, it would make thing get slower
        """
        sentence_text = self.sentence.document.text[self.sentence.index]
        # Get the relative position in the sentence
        if len(self.sentence) > 0:
            pos_l_extend = int(self.l_extend) - int(self.sentence[0].l_extend)
            original_text = sentence_text[pos_l_extend: pos_l_extend
                                           + int(self.r_extend) - int(self.l_extend)]
        else:
            original_text = sentence_text[: int(self.r_extend) - int(self.l_extend)]
        if original_text != self.content:
            """
            A weird way to fix the problem, not really a good approach
            """
            self.content = self.lemma = original_text.replace(' ', REPLACE_SPACE)


    def set_head (self, head):
        self.head = head
    
    def __str__(self):
        return self.content

class Parsed_Sentence:
    def __init__(self, token_array, sentence_counter, document):
        self.index = sentence_counter
        self.tokens = []
        self.document = document
        for token in token_array:
            parsed_token = Parsed_Token(token, self)
            self.tokens.append(parsed_token)
        self.tree = None

    def set_tree(self, tree_repr):
        self.tree = Tree(tree_repr)

    def set_dependency( self, dependency_repr):
        value_error = False
        for (dep_type, dep_head_str,
             dep_dep_str, dep_head_index,
             dep_dep_index) in dependency_repr:
            try:
                dep_dep_index = re.match(r'\d*',dep_dep_index).group(0)
                dep_head_index = re.match(r'\d*',dep_head_index).group(0)
                if int(dep_dep_index) < len(self.tokens):
                    self.tokens[int(dep_dep_index)].set_head(
                        self.tokens[int(dep_head_index)])
            except ValueError as ve:
                print ve
                print (dep_type, dep_head_str,
                     dep_dep_str, dep_head_index,
                     dep_dep_index)
            except IndexError as ie:
                print ie
    
    def __str__(self):
        return ' '.join([str(token) for token in self.tokens])      

    def __iter__(self):
        return iter(self.tokens)
    
    def __getitem__(self, key):
        return self.tokens[key]
    
    def __len__(self):
        return len(self.tokens)
    
class Parsed_Document:
    def __init__(self, doc_dict):
        self.sentences = []
        self.text = doc_dict[TEXT]
        sentence_counter = 0
        for token_array, dependency_repr, tree in zip(
            doc_dict[TOKEN], doc_dict[DEPENDENCY],
            doc_dict[TREE]):
            new_sentence = Parsed_Sentence( token_array, sentence_counter, self )
            sentence_counter += 1
            new_sentence.set_tree(tree)
            new_sentence.set_dependency(dependency_repr)
            self.sentences.append(new_sentence)
        
        
    
    def set_coreference( self, coref_str ):
        """
        This method should be left for later
        implementation as I haven't found any way
        to use coreference for the task at hand
        """
        pass

    def __iter__( self ):
        return iter(self.sentences)
    
    def __getitem__(self, key):
        return self.sentences[key]
    
    def __len__(self):
        return len(self.sentences)
