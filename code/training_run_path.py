import sys, os
from ttk_path import TTK_ROOT

if sys.platform[:3] == "win":
    SLASH = '\\'
elif sys.platform[:3] == "lin":
    SLASH = '/'
    
TBAQ_FOLDER = 'TBAQ-cleaned'
AQUAINT_FOLDER = 'AQUAINT'
TIMEBANK_FOLDER = 'TimeBank'
SILVER_FOLDER = 'TE3-Silver-data'
PLATINUM_FOLDER = 'te3-platinumstandard' + SLASH + 'te3-platinum'
GOLD_INPUT_PATHS = [os.path.join(TBAQ_FOLDER, AQUAINT_FOLDER),
                    os.path.join(TBAQ_FOLDER, TIMEBANK_FOLDER) 
                       ]
SILVER_INPUT_PATHS = [SILVER_FOLDER]
TEST_INPUT_PATHS = [PLATINUM_FOLDER]
DATA_PATH = os.path.join(TTK_ROOT, 'data')
INPUT_DATA_PATH = os.path.join(DATA_PATH, 'in')
FEATURES_DATA_PATH = os.path.join(DATA_PATH, 'features')
OUTPUT_DATA_PATH = os.path.join(DATA_PATH, 'out')
TEMPO_DATA_PATH = os.path.join(DATA_PATH, 'tmp')
LOG_DATA_PATH = os.path.join(DATA_PATH, 'logs')
BETWEEN_COMMAND_TEMPO_PATH = os.path.join(DATA_PATH, 'global_tmp')

GOLD_PROBLEM = 'gold'
SILVER_PROBLEM = 'silver'
TEST_PROBLEM = 'test'

FEATURES_SUFFIX = '_features'
PROBLEM_SUFFIX = '_problem'
QUOTE_CLEAN_SUFFIX = '.quoted_cleaned'
RUN_SUFFIX = '_run.txt'

MERGED_FILE_SUFFIX = '.pre.merged.xml'
TIMEBANK_SUFFIX = '*.tml'

SVM_FEATURES_DATA_PATH = os.path.join(DATA_PATH, 'svm_features')
SVM_FEATURES_DATA_PATH_WITH_NARRATIVE = os.path.join(DATA_PATH, 'svm_features_with_narrative')
MERGED_FILE_SUFFIX_PARSED = '.parsed.pre.merged.xml'
SVM_BETWEEN_COMMAND_TEMPO_PATH = os.path.join(DATA_PATH, 'global_tmp_svm')