from ttk_path import TTK_ROOT
from tarsqi import run_tarsqi
import os, sys
import glob
from utilities.preprocessing_event_time_merger import merger
import shutil
import glob
from utilities import cleaner, logger
from library.tarsqi_constants import PREPROCESSOR, TRAIN_CLASSIFIER
from utilities.stanford.parse_data import TreeParser
from training_run_path import *

def _collect_train_test_files():
    # Make sure we're in the right directory. If the toolkit
    # crached on a previous file it may end up being in a
    # different directory.
    os.chdir(TTK_ROOT)
    
    # Add all gold training file names to an array
    gold_training_files = []
    for folder in GOLD_INPUT_PATHS:
        gold_training_files += glob.glob(os.path.join(INPUT_DATA_PATH, folder, TIMEBANK_SUFFIX))
    
    # Add all silver training file names to an array
    silver_training_files = []
    for folder in SILVER_INPUT_PATHS:
        silver_training_files += glob.glob(os.path.join(INPUT_DATA_PATH, folder, TIMEBANK_SUFFIX))
    
    # Add all silver training file names to an array
    testing_files = []
    for folder in TEST_INPUT_PATHS:
        testing_files += glob.glob(os.path.join(INPUT_DATA_PATH, folder, TIMEBANK_SUFFIX))
    
    return (gold_training_files, silver_training_files, testing_files)   

def _run_preprocessing(filename, full_filename):
    output_filename = os.path.join(OUTPUT_DATA_PATH, filename)
    args = ['timebank', 'pipeline=%s' %PREPROCESSOR, full_filename, output_filename]
    run_tarsqi(args)

def _run_merging(problem_name, filename, full_filename):
    preprocessing_file_output = os.path.join(TEMPO_DATA_PATH,
                                             filename + '.pre.xml')
    fix_merged_file(preprocessing_file_output)
    tempo_path = os.path.join(BETWEEN_COMMAND_TEMPO_PATH, problem_name)
    tempo_merged_file = os.path.join(tempo_path,
                                    filename + MERGED_FILE_SUFFIX)
    merger(preprocessing_file_output, full_filename, tempo_merged_file)
    fix_merged_file(tempo_merged_file)
    return tempo_merged_file

def _run_training_classifier(tempo_merged_file, filename, feature_path):
#     # Run tarsqi again with the merged input training file
#     # This time with TRAIN_CLASSIFIER, just to extract the features
#       
    args = ['timebank', 'pipeline=%s' % TRAIN_CLASSIFIER,
            tempo_merged_file, os.path.join(OUTPUT_DATA_PATH, filename + '.cla.trained.xml')]
    run_tarsqi(args)
    # Copy two features files to the training features folder
    ee_fragment_files = glob.glob(os.path.join(TEMPO_DATA_PATH, '*.train.EE'))
    et_fragment_files = glob.glob(os.path.join(TEMPO_DATA_PATH, '*.train.ET'))
           
    EE_FEATURES_PATH = os.path.join(feature_path, 'ee')
    ET_FEATURES_PATH = os.path.join(feature_path, 'et')
    for fragment_file in ee_fragment_files:
        relative_fragment_file_name = fragment_file[fragment_file.rindex(SLASH) + 1:]
        shutil.copyfile(fragment_file, os.path.join(EE_FEATURES_PATH,
                                                    filename + '.' + 
                                                    relative_fragment_file_name))
            
    for fragment_file in et_fragment_files:
        relative_fragment_file_name = fragment_file[fragment_file.rindex(SLASH) + 1:]
        shutil.copyfile(fragment_file, os.path.join(ET_FEATURES_PATH,
                                                    filename + '.' + 
                                                    relative_fragment_file_name))

def _feature_extraction(problem_name, full_filename, 
                        feature_path, with_existed_merged_file = False):
    """
    """
    filename = full_filename[full_filename.rindex(SLASH) + 1:]
    
    if  with_existed_merged_file:
        tempo_path = os.path.join(BETWEEN_COMMAND_TEMPO_PATH, problem_name)
        tempo_merged_file = os.path.join(tempo_path,
                                    filename + MERGED_FILE_SUFFIX)
    else:
        _run_preprocessing(filename, full_filename)
        tempo_merged_file = _run_merging(problem_name, filename, full_filename)
    #Sometimes tempo_merged_file doesn't exist at all
    # because of problem in preprocessing
    try:
        open(tempo_merged_file, 'r')
        _run_training_classifier(tempo_merged_file, filename, feature_path)
    except Exception as e:
        print str(e)

def fix_merged_file(input_file):
    # There is some problem in writing escape characters in window
    # so I just basically replace the character for the heading of the 
    # merged file
    # Incorrect character is &lt; = < and &gt; = >
    correct_tags = [('&lt;', '<'), ('&gt;', '>')]
    buffer = ''
    tempo_file = open(input_file, 'r')
    for line in tempo_file:
        for tag in correct_tags:
            line = line.replace(tag[0], tag[1])
        buffer += line
    tempo_file.close()
    tempo_file = open(input_file, 'w')
    tempo_file.write(buffer)
    tempo_file.close()

def _feature_extract(problem_name, filelist, path, problematic_filename, silent, with_existed_merged_file = False):
    
    problematic_files = []
    for file in filelist:
        cleaner.quote_cleaner(file, file + QUOTE_CLEAN_SUFFIX)
        if silent:
            try:
                _feature_extraction(problem_name, 
                                    file + QUOTE_CLEAN_SUFFIX, path, with_existed_merged_file)
            except Exception:
                problematic_files.append(file + QUOTE_CLEAN_SUFFIX)
        else:
            _feature_extraction(problem_name, 
                                file + QUOTE_CLEAN_SUFFIX, path, with_existed_merged_file)
    
    if problematic_filename != None:
        problematic_filename = os.path.join(LOG_DATA_PATH, problematic_filename)
        if problematic_filename.endswith(QUOTE_CLEAN_SUFFIX):
            problematic_filename = problematic_filename[:-len(QUOTE_CLEAN_SUFFIX)]
        f = open(problematic_filename, 'w')
        for file in problematic_files:
            logger.error('========================PROBLEM===========================')
            logger.error(file)
            f.write(file)
            f.write('\n')
        f.close()

# _feature_extract( gold_training_files, GOLD_FEATURES_PATH, 
#                   )
# _feature_extract( silver_training_files[:100], SILVER_FEATURES_PATH, 'silver_problem.txt')

def _get_problematic_files (problematic_filename):
    problematic_filename = os.path.join(LOG_DATA_PATH, problematic_filename)
    f = open(problematic_filename, 'r')
    file_names = []
    for line in f:
        file_name = line.strip()
        file_names.append(file_name)
    return file_names


def _run_extract_log_problem(problem_name, 
                             run, with_existed_merged_file = False):
    
    OLD_PROBLEM_FILE = problem_name + '_%d' % (run - 1) + RUN_SUFFIX
    NEW_PROBLEM_FILE = problem_name + '_%d' % run + RUN_SUFFIX
    if run == 1:
        problem_files = t_files[problem_name]
    else:
        problem_files = _get_problematic_files(OLD_PROBLEM_FILE)
    print problem_files
    FEATURES_PATH = os.path.join(FEATURES_DATA_PATH, problem_name)
    _feature_extract(problem_name, problem_files, FEATURES_PATH, 
                     NEW_PROBLEM_FILE, False, with_existed_merged_file)

gold_training_files, silver_training_files, testing_files = _collect_train_test_files()
t_files = {GOLD_PROBLEM: gold_training_files[:1],
           SILVER_PROBLEM: silver_training_files,
           TEST_PROBLEM: testing_files}

"""
Original run
"""
_run_extract_log_problem(GOLD_PROBLEM, 1)
#_run_extract_log_problem(SILVER_PROBLEM, 1)
#_run_extract_log_problem(TEST_PROBLEM, 1)

"""
Run without preprocessing
"""
# _run_extract_log_problem(GOLD_PROBLEM, 1, True)
# _run_extract_log_problem(SILVER_PROBLEM, 1, True)
# _run_extract_log_problem(TEST_PROBLEM, 1, True)


