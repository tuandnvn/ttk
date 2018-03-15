import os
from ttk_path import TTK_ROOT
import fnmatch

def change_suffix(directory, input_filter, input_replace, output_replace):
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, input_filter):
            old_file = os.path.join(root, filename)
#             print old_file
            new_file = old_file[:-len(input_replace)] + output_replace
#             print new_file
            os.rename(old_file, new_file)

DIR = os.path.join(TTK_ROOT, 'data', 'raw_result')
change_suffix(DIR, '*.tml.fragment_001.cla.i.xm.result', 
              '.tml.fragment_001.cla.i.xm.result', 
              '.result')