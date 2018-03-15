from ttk_path import TTK_ROOT
from utilities.tlink_change import tlink_inject, tlink_remove
# from utilities.tlink_inject_with_prior import tlink_inject_with_prior as tiwp
# from utilities.tlink_inject_with_prior_with_check import tlink_inject_with_prior_with_check as tiwpwc
import glob
import os
import logging
from library.dataSpec import *

# logging.basicConfig(filename=os.path.join(TTK_ROOT, 'data', 'logs', 
#                                           'incorporate_link.log'),
#                     level=logging.DEBUG)
logging.basicConfig(filename=os.path.join(TTK_ROOT, 'data', 'logs', 
                                          'incorporate_link_with_prior_with_check.log'),
                    level=logging.DEBUG)



def incorporate_tlink( no_tlink_directory, result_directory, tlink_directory ):
    result_files = glob.glob(os.path.join(result_directory, 
                                            '*%s' % RESULT_SUFFIX))
    for result_file in result_files:
        rel_filename = result_file[result_file.rindex(os.path.sep) + 1:]
        no_tlink_file = os.path.join(no_tlink_directory,
                                       '%s%s' % (rel_filename[:-len(RESULT_SUFFIX)],
                                    NO_TLINK_SUFFIX) )
        tlink_file = os.path.join(tlink_directory,
                                  '%s%s' % (rel_filename[:-len(RESULT_SUFFIX)],
                                    ADD_TLINK_SUFFIX) )
#         try:
        logging.info("=================================================")
        logging.info("%s" % no_tlink_file)
        tlink_inject(no_tlink_file, result_file, tlink_file)
#         except Exception as e:
#             logging.error(e)


def incorporate_tlink_with_prior( no_tlink_directory, result_directory, 
                                  tlink_directory, original_directory = None):
    result_files = glob.glob(os.path.join(result_directory, 
                                            '*%s' % RESULT_SUFFIX))
    total_fix_label_counter = 0
    total_worsen_label_counter = 0
    for result_file in result_files:
        rel_filename = result_file[result_file.rindex(os.path.sep) + 1:]
        no_tlink_file = os.path.join(no_tlink_directory,
                                       '%s%s' % (rel_filename[:-len(RESULT_SUFFIX)],
                                    NO_TLINK_SUFFIX) )
        tlink_file = os.path.join(tlink_directory,
                                  '%s%s' % (rel_filename[:-len(RESULT_SUFFIX)],
                                    ADD_TLINK_SUFFIX) )
        if original_directory != None:
            original_file = os.path.join(original_directory,
                                           '%s%s' % (rel_filename[:-len(RESULT_SUFFIX)],
                                        ORIGINAL_SUFFIX) )
            
            (fix_label_counter, 
             worsen_label_counter) = tiwpwc(no_tlink_file, result_file,
                                             tlink_file, original_file)
            total_fix_label_counter += fix_label_counter
            total_worsen_label_counter += worsen_label_counter
        else:
            tiwp(no_tlink_file, result_file, tlink_file)
    logging.info("=========================TOTAL============================")
    logging.info("==========================================================")
    logging.info("===FIX===")
    logging.info(total_fix_label_counter)
    logging.info("===WORSEN===")
    logging.info(total_worsen_label_counter)
    
def remove_tlink( original_directory, no_tlink_directory):
    print os.path.join(original_directory, 
                                            '*%s' % ORIGINAL_SUFFIX)
    original_files = glob.glob(os.path.join(original_directory, 
                                            '*%s' % ORIGINAL_SUFFIX))
    for original_file in original_files:
        print original_file
        rel_filename = original_file[original_file.rindex(os.path.sep) + 1:]
        no_tlink_file = os.path.join(no_tlink_directory,
                                       '%s%s' % (rel_filename[:-len(ORIGINAL_SUFFIX)],
                                    NO_TLINK_SUFFIX) )
        try:
            tlink_remove ( original_file, no_tlink_file)
        except Exception as e:
            logging.error(e)

"""
{"main_events_in_consecutive_sentences": {"1": [[["SIMULTANEOUS", [1, 1.0958849]]
"""
RESULT_DIRECTORY_OLD_FORMAT = os.path.join(TTK_ROOT, 'data', 'raw_result_old_format')


"""
{"main_events_in_consecutive_sentences": {"1": {"Result_dict": {"('SIMULTANEOUS', 'AFTER')":
 1.0958849, "('AFTER', 'BEFORE')": -2.1010391, "('SIMULTANEOUS', 'BEFORE')":
"""
RESULT_DIRECTORY_NEW_FORMAT = os.path.join(TTK_ROOT, 'data', 'raw_result_new_format')

RESULT_DIRECTORY_NEW_FORMAT_GOLD_TEST =\
 os.path.join(TTK_ROOT, 'data', 'raw_result_new_format_gold_test')



RESULT_DIRECTORY_NEW_FORMAT_WITH_NARRATIVE = os.path.join(TTK_ROOT, 
                                                          'data', 
                                                          'raw_result_with_narrative')
RESULT_DIRECTORY_SILVER_SPLIT = os.path.join(TTK_ROOT, 
                                              'data', 
                                              'raw_result_silver_split')
"""
When we don't use prior (the first approach)
"""
ADDED_TLINK_DIRECTORY = os.path.join(TTK_ROOT, 'data', 'added_tlink')

ADDED_TLINK_GOLD_TEST_DIRECTORY = os.path.join(TTK_ROOT, 'data', 'added_tlink_gold_test')

"""
When we use narrative scheme as priors
"""
ADDED_TLINK_DIRECTORY_WITH_PRIOR = os.path.join(TTK_ROOT, 'data', 'added_tlink_with_prior')

"""
When we use narrative scheme as features
"""
ADDED_TLINK_DIRECTORY_WITH_NARRATIVE = os.path.join(TTK_ROOT, 
                                                    'data', 
                                                    'added_tlink_with_narrative')
"""
Silver split
"""
ADDED_TLINK_SILVER_SPLIT_DIRECTORY = os.path.join(TTK_ROOT,
                                                   'data',
                                                    'added_tlink_silver_split')
ADDED_TLINK_SILVER_SPLIT_DIRECTORY_WITH_PRIOR = os.path.join(TTK_ROOT,
                                                   'data',
                                                    'added_tlink_silver_split_with_prior')

"""
Silver split with narrative features
"""
RESULT_DIRECTORY_SILVER_SPLIT_NARRATIVE = os.path.join(TTK_ROOT, 
                                              'data', 
                                              'raw_result_silver_split_with_narrative')

ADDED_TLINK_SILVER_SPLIT_DIRECTORY_WITH_NARRATIVE = os.path.join(TTK_ROOT,
                                                   'data',
                                                    'added_tlink_silver_split_with_narrative')


incorporate_tlink( TEST_NO_TLINK_DIRECTORY, 
                   RESULT_DIRECTORY_NEW_FORMAT, 
                   ADDED_TLINK_DIRECTORY)

# incorporate_tlink_with_prior( TEST_NO_TLINK_DIRECTORY, 
#                               RESULT_DIRECTORY_NEW_FORMAT, 
#                               ADDED_TLINK_DIRECTORY,
#                               TEST_DIRECTORY)

# remove_tlink(SILVER_DIRECTORY, SILVER_NO_TLINK_DIRECTORY)
# incorporate_tlink( TEST_NO_TLINK_DIRECTORY, 
#                    RESULT_DIRECTORY_NEW_FORMAT_WITH_NARRATIVE, 
#                    ADDED_TLINK_DIRECTORY_WITH_NARRATIVE)

"""
Split silver data
"""
# incorporate_tlink( SILVER_NO_TLINK_DIRECTORY, 
#                    RESULT_DIRECTORY_SILVER_SPLIT, 
#                    ADDED_TLINK_SILVER_SPLIT_DIRECTORY)
# incorporate_tlink_with_prior( SILVER_NO_TLINK_DIRECTORY, 
#                               RESULT_DIRECTORY_SILVER_SPLIT, 
#                               ADDED_TLINK_SILVER_SPLIT_DIRECTORY_WITH_PRIOR,
#                               SILVER_DIRECTORY)

# incorporate_tlink( SILVER_NO_TLINK_DIRECTORY, 
#                    RESULT_DIRECTORY_SILVER_SPLIT_NARRATIVE, 
#                    ADDED_TLINK_SILVER_SPLIT_DIRECTORY_WITH_NARRATIVE)

# incorporate_tlink( GOLD_NO_TLINK_DIRECTORY, 
#                    RESULT_DIRECTORY_NEW_FORMAT_GOLD_TEST, 
#                    ADDED_TLINK_GOLD_TEST_DIRECTORY)
# remove_tlink(GOLD_DIRECTORY[0], GOLD_NO_TLINK_DIRECTORY)
# remove_tlink(GOLD_DIRECTORY[1], GOLD_NO_TLINK_DIRECTORY)