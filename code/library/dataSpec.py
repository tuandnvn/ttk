from ttk_path import TTK_ROOT
import os

RESULT_SUFFIX = '.result'
ADD_TLINK_SUFFIX = '.tml'
NO_TLINK_SUFFIX = '.notlink.tml'
ORIGINAL_SUFFIX = '.tml'

TEST_DIRECTORY  = os.path.join(TTK_ROOT, 'data', 'in', 
                                'te3-platinumstandard', 'te3-platinum')
SILVER_DIRECTORY  = os.path.join(TTK_ROOT, 'data', 'in',
                                 'TE3-Silver-data')
GOLD_DIRECTORY = [ os.path.join(TTK_ROOT, 'data', 'in',
                                 'TBAQ-cleaned', 'AQUAINT'), 
                  os.path.join(TTK_ROOT, 'data', 'in',
                                 'TBAQ-cleaned', 'TimeBank')]
NO_TLINK_DIRECTORY = os.path.join(TTK_ROOT, 'data', 'no_tlink')
TEST_NO_TLINK_DIRECTORY = os.path.join(NO_TLINK_DIRECTORY , 'test')
GOLD_NO_TLINK_DIRECTORY = os.path.join(NO_TLINK_DIRECTORY , 'gold')
SILVER_NO_TLINK_DIRECTORY = os.path.join(NO_TLINK_DIRECTORY , 'silver')


SILVER_TRAINING_SET = 'silver_traning_set'
SILVER_TESTING_SET = 'silver_testing_set'

