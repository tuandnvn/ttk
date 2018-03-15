from ttk_path import TTK_ROOT
from library.dataSpec import SILVER_DIRECTORY, ORIGINAL_SUFFIX, \
                            SILVER_TRAINING_SET, SILVER_TESTING_SET
import os
import json
import random
import glob
import bisect
import shutil

def find_file_name( relative_file_name , training_files ):
    index = bisect.bisect_left(training_files, relative_file_name)
    if index >= len(training_files):
        return False
    if training_files[index] != relative_file_name:
        return False
    return True

def randomize_split ( filenames, output_log, training_size):
    """
    Split the silver data set into two datasets
    Parameters:
        - filenames: the list of filenames to be split
        - output_log: log the names of the training and testing files (relative
                    name onlhy)
        - training_size: size of the training set
    """
    
    random.shuffle( filenames )
    
    training_files = [filename[filename.rfind(os.path.sep) + 1:-len(ORIGINAL_SUFFIX)] 
                      for filename in filenames[:training_size]]
    testing_files = [filename[filename.rfind(os.path.sep) + 1:-len(ORIGINAL_SUFFIX)] 
                     for filename in filenames[training_size:]]
    
    data = {SILVER_TRAINING_SET : sorted(training_files), 
            SILVER_TESTING_SET : sorted(testing_files)}
    
    samples = {}
    try:
        with open(output_log, 'r') as output_log_file:
            samples = json.load(output_log_file)
    except Exception:
        print 'File doesn\'t exist'
    with open(output_log, 'w') as output_log_file:
        code = random.randint(1000000000,9999999999)
        while code not in samples:
            samples[code] =  data
        json.dump(samples , output_log_file)

# print os.path.join ( SILVER_DIRECTORY , '*'  + ORIGINAL_SUFFIX)
silver_filenames = glob.glob( os.path.join ( SILVER_DIRECTORY , '*'  + ORIGINAL_SUFFIX) )
output_log = os.path.join( TTK_ROOT , 'data' , 'dict' , 'split.dict')

# randomize_split(silver_filenames, output_log, 2000)

"""
Just need to run one time
"""
SILVER_SPLIT_TEST_DIRECTORY = os.path.join( TTK_ROOT, 'data', 'silver_split_test' )
ADDED_TLINK_SILVER_SPLIT_DIRECTORY = os.path.join( TTK_ROOT, 'data', 'added_tlink_silver_split_with_narrative' )
test_files = glob.glob(os.path.join( ADDED_TLINK_SILVER_SPLIT_DIRECTORY, 
                                     '*' + ORIGINAL_SUFFIX ))
for test_file in test_files:
    test_file_rel = test_file[test_file.rfind(os.path.sep) + 1:]
    original_file_name = os.path.join( SILVER_DIRECTORY,  test_file_rel)
    copy_file_name = os.path.join( SILVER_SPLIT_TEST_DIRECTORY,  test_file_rel)
    shutil.copy(original_file_name, copy_file_name)
