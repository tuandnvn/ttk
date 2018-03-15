"""
 
Python wrapper around the MaxEnt Classifier
 
CLASSES
   ClassifierWrapper
    
"""
 
import os
 
from ttk_path import TTK_ROOT
from library.tarsqi_constants import CLASSIFIER
from library.timeMLspec import TLINK, EIID, TID
from library.timeMLspec import RELTYPE, EVENT_INSTANCE_ID, TIME_ID
from library.timeMLspec import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME, CONFIDENCE
from components.common_modules.component import ComponentWrapper
from utilities import logger
from components.classifier import vectors, tree_vectors,\
                             tree_vectors_with_narrative
from docmodel.xml_parser import Parser
from docmodel.xml_parser import XmlDocElement, XmlDocument
from adjacent_tlink_feature_extractor import feature_recollect
from feature_index import Feature_Index_Dict
 
PARSED_DOCUMENT = 'PARSED_DOC'

class ClassifierWrapper(ComponentWrapper):
 
    """Wraps the maxent link classifier."""
    def __init__(self, tag, xmldoc, tarsqi_instance, auxillary = None):
 
        """Calls __init__ on the base class and initializes component_name,
        DIR_CLASSIFIER, CREATION_EXTENSION, TMP_EXTENSION and
        RETRIEVAL_EXTENSION."""
        ComponentWrapper.__init__(self, tag, xmldoc, tarsqi_instance)
        self.component_name = CLASSIFIER
        self.DIR_CLASSIFIER = os.path.join(TTK_ROOT, 'components', 'classifier')
        self.CREATION_EXTENSION = 'cla.i.xml'
        self.TMP_EXTENSION = 'cla.t.xml'
        self.RETRIEVAL_EXTENSION = 'cla.o.xml'
        self.DIR_DATA = os.path.join(TTK_ROOT, 'data', 'tmp')
        self.DICT_DATA = os.path.join(TTK_ROOT, 'data', 'dict')
         
#         platform = self.document.getopt_platform()
#         if platform == 'linux2':
#             self.executable = 'mxtest.opt.linux'
#         elif platform == 'darwin':
#             self.executable = 'mxtest.opt.osx'
        self.executable = 'mxtest.opt.linux'
        self.auxillary = auxillary
         
    def process_fragments(self):
        """Retrieve the XmlDocument and hand it to the classifier for processing. Processing will
        update this slice when tlinks are added."""
  
        os.chdir(self.DIR_CLASSIFIER)
        perl = self.tarsqi_instance.getopt_perl()
        
        ee_model = os.path.join('data', 'op.e-e.model')
        et_model = os.path.join('data', 'op.e-t.model')
  
        fragment_count = 0
          
        for fragment in self.fragments:
            base = fragment[0]
            fragment_count += 1
              
            fin = os.path.join(self.DIR_DATA, base+'.'+self.CREATION_EXTENSION)
            ftmp = os.path.join(self.DIR_DATA, base+'.'+self.TMP_EXTENSION)
            fout = os.path.join(self.DIR_DATA, base+'.'+self.RETRIEVAL_EXTENSION)
              
            ee_vectors = fin + '.EE'
            et_vectors = fin + '.ET'
            ee_results = ee_vectors + '.REL'
            et_results = et_vectors + '.REL'
             
            fragment_doc = Parser().parse_file(open(fin, "r")) 
            vectors.create_vectors(fragment_doc, ee_vectors, et_vectors)
             
            print 'done create vectors'
  
            commands = [
                "./%s -input %s -model %s -output %s > class.log" %
                (self.executable, ee_vectors, ee_model, ee_results),
                "./%s -input %s -model %s -output %s > class.log" %
                (self.executable, et_vectors, et_model, et_results),
                "%s collectClassifier.pl %s %s %s" % 
                (perl, ee_vectors, et_vectors, ftmp)  ]
            for command in commands:
                os.system(command)
             
            print 'done create features'
            self._add_tlinks_to_fragment(fin, ftmp, fout)


    def process_training_fragments(self):
        """Retrieve the TRAINING XmlDocument and hand it to the feature extracter for processing. 
        Features file will be used for training"""
  
        os.chdir(self.DIR_CLASSIFIER)
        perl = self.tarsqi_instance.getopt_perl()
  
        fragment_count = 0
        
        for fragment in self.fragments:
            base = fragment[0]
            fragment_count += 1
              
            fin = os.path.join(self.DIR_DATA, base+'.'+self.CREATION_EXTENSION)
              
            ee_vectors = fin + '.EE'
            et_vectors = fin + '.ET'
#             tt_vectors = fin + '.TT'
            ee_train_vectors = fin + '.train.EE'
            et_train_vectors = fin + '.train.ET'
#             tt_train_vectors = fin + '.train.TT'
             
            fragment_doc = Parser().parse_file(open(fin, "r"))
            fragment_doc.set_dct_timex( self.document.get_dct() ) 
#             vectors.create_vectors(fragment_doc, ee_vectors, et_vectors, tt_vectors)
#             vectors.create_vectors(fragment_doc, ee_vectors, et_vectors)
            """
            Without narrative scheme
            """
            dictionary_file = os.path.join( self.DICT_DATA, 
                                            'feature_index.dict')
            """
            With narrative scheme
            """
#             dictionary_file = os.path.join( self.DICT_DATA, 
#                                             'feature_index_with_narrative_scheme.dict' )
            feature_index_dict = Feature_Index_Dict()
            feature_index_dict.load_from_file(dictionary_file)
            
            """
            Without narrative scheme
            """
            tree_vectors.create_vectors(fragment_doc, self.auxillary[PARSED_DOCUMENT], 
                                        feature_index_dict, ee_vectors, et_vectors)
            """
            With narrative scheme
            """
#             tree_vectors_with_narrative.create_vectors(fragment_doc, self.auxillary[PARSED_DOCUMENT], 
#                                         feature_index_dict, ee_vectors, et_vectors)
            feature_index_dict.dump_to_file(dictionary_file)
            print 'done create vectors'
#             feature_recollect( self.document, ee_vectors, et_vectors, tt_vectors,
#                                ee_train_vectors, et_train_vectors, tt_train_vectors)
            feature_recollect( self.document, ee_vectors, et_vectors,
                               ee_train_vectors, et_train_vectors)
            print 'done collect training label and features'
            print '======================================================'
  
        
    def _add_tlinks_to_fragment(self, in_fragment, tmp_fragment, out_fragment):

        """Takes the links created by the classifier and merges them into the
        input fragment."""

        xmldoc1 = Parser().parse_file(open(in_fragment,'r'))
        xmldoc2 = Parser().parse_file(open(tmp_fragment,'r'))

        for tlink in xmldoc2.get_tags(TLINK):
            reltype = tlink.attrs[RELTYPE]
            id1 = tlink.attrs.get(EVENT_INSTANCE_ID, None)
            if not id1:
                id1 = tlink.attrs.get(TIME_ID, None)
            if not id1:
                logger.warn("Could not find id1 in " + tlink.content)
            id2 = tlink.attrs.get(RELATED_TO_EVENT_INSTANCE, None)
            if not id2:
                id2 = tlink.attrs.get(RELATED_TO_TIME, None)
            if not id2:
                logger.warn("Could not find id2 in " + tlink.content)
            origin = CLASSIFIER + ' ' + tlink.attrs.get(CONFIDENCE,'')
            xmldoc1.add_tlink(reltype, id1, id2, origin)

        xmldoc1.save_to_file(out_fragment)
        
    def _add_links_to_xmldoc(self, xmldoc, ee_vectors, et_vectors, ee_results, et_results, fout):
 
        """Insert new tlinks into the xmldco using the vectors and the results
        from the classifier."""
         
        for (f1, f2) in ((ee_vectors, ee_results), (et_vectors, et_results)):
            vector_file = open(f1)
            classifier_file = open(f2)
            for line in vector_file:
                classifier_line = classifier_file.readline()
                attrs = self._parse_vector_string(line)
                id1 = self._get_id('0', attrs, line)
                id2 = self._get_id('1', attrs, line)
                (rel, confidence) = self._parse_classifier_line(classifier_line)[0:2]
                origin = CLASSIFIER + ' ' + confidence
                xmldoc.add_tlink(rel, id1, id2, origin)
 
 
    def _parse_vector_string(self, line):
 
        """Return the attribute dictionaries from the vestor string. """
         
        attrs = {}
        for pair in line.split():
            if pair.find('-') > -1:
                (attr, val) = pair.split('-',1)
                attrs[attr] = val
        return attrs
 
     
    def _parse_classifier_line(self, line):
 
        """Extract relType, confidence correct/incorrect and correct relation
        from the classifier result line."""
         
        line = line.strip()
        (rel, confidence, judgment, correct_judgement) = line.split()
        return (rel, confidence, judgment, correct_judgement)
 
 
    def _get_id(self, prefix, attrs, line):
 
        """Get the eiid or tid for the first or second object in the
        vector. The prefix is '0' or '1' and determines which object's
        id is returned."""
         
        id = attrs.get(prefix+EIID, attrs.get(prefix+TID, None))
        if not id:
            logger.warn("Could not find id in " + line)
        return id
