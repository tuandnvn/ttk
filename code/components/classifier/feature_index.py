import json

class Feature_Index_Dict:
    def __init__(self):
        self._label_to_index = {}
        self._index_to_label = []
    
    def _add_label(self, label):
        if label in self._label_to_index:
            return 
        self._label_to_index[label] = len(self._index_to_label)
        self._index_to_label.append(label)
        return self._label_to_index[label]
    
    def get_index(self, label):
        if label in self._label_to_index:
            return self._label_to_index[label]
        else:
            return self._add_label(label)
    
    def get_label(self, index):
        if index >=0 and index < len(self._index_to_label):
            return self._index_to_label[index]
    
    def dump_to_file(self, file_name):
        with open(file_name, 'w') as json_file:
            json.dump(self._index_to_label, json_file)
    
    def load_from_file(self, file_name):
        try:
            with open(file_name, 'r') as json_file:
                self._index_to_label = json.load(json_file)
                self._label_to_index = {}
                for i in xrange(len(self._index_to_label)):
                    self._label_to_index[self._index_to_label[i]] = i
        except IOError as e:
            print 'JSON file to load feature doesn\'t exist'
        