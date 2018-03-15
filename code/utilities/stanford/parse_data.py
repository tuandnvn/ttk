import json
from jsonrpc import ServerProxy, JsonRpc20, TransportTcpIp
import shelve as sh
from docmodel.xml_parser import Parser

DEFAULT_PORT = 2346
DEFAULT_HOST = '127.0.0.1'

class StanfordNLP:
    def __init__(self):
        self.server = ServerProxy(JsonRpc20(),
                                  TransportTcpIp(addr=(DEFAULT_HOST, DEFAULT_PORT)))
    
    def parse(self, text):
        return json.loads(self.server.parse(text))

class TreeParser():
    def __init__(self):
        self.__nlpParser__ = StanfordNLP()
    
    def parse(self, input_file, output_file):
        print ' ================= Parsing ==================='
        input_xml_doc = Parser().parse_file(open(input_file, "r"))
        
        inside_text = False;
        plain_text = ''
        for element in input_xml_doc:
            if inside_text:
                if not element.is_tag() and not element.is_space():
                    plain_text += element.content
            if element.is_opening_tag() and element.tag == 'TEXT':
                inside_text = True
            if element.is_closing_tag() and element.tag == 'TEXT':
                inside_text = False
        
#         print   plain_text 
        plain_text = 'I love to eat.'
        result = self.__nlpParser__.parse(plain_text)
        shelf_file = sh.open(output_file)
         
        for key in result:
            shelf_file[key] = result[key]
        shelf_file.close()
