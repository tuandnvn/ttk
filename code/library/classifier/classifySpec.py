from library.tlink_relation import AFTER, BEFORE, NORELATION, \
                                    SIMULTANEOUS, IS_INCLUDED, INCLUDES

EE_FLAG_MAIN_INTRA_SENT = 'main_event_and_other_event_in_sentence'
EE_FLAG_MAIN_INTER_SENT = 'main_events_in_consecutive_sentences'
EE_FLAG_CONSE_SENT = 'consecutive_events_in_sentence'
ET_FLAG_CONSE_SENT = 'consecutive_event_and_time_in_sentence'
ET_FLAG_WITH_DCT = 'event_and_dct_time_in_sentence'

KEEP_FEATURES = { EE_FLAG_MAIN_INTRA_SENT: {AFTER:AFTER, BEFORE:BEFORE, NORELATION:NORELATION},
                  EE_FLAG_MAIN_INTER_SENT: {SIMULTANEOUS:SIMULTANEOUS, AFTER:AFTER, BEFORE:BEFORE},
                  ET_FLAG_CONSE_SENT: {IS_INCLUDED:IS_INCLUDED, INCLUDES:INCLUDES,
                       NORELATION:NORELATION},
                  ET_FLAG_WITH_DCT:{SIMULTANEOUS:SIMULTANEOUS, AFTER:AFTER, BEFORE:BEFORE}}

# KEEP_FEATURES = {EE_FLAG_MAIN_INTRA_SENT:{AFTER:AFTER, BEFORE:BEFORE, NORELATION:NORELATION},  
#                  EE_FLAG_MAIN_INTER_SENT: {SIMULTANEOUS:SIMULTANEOUS, NORELATION:NORELATION, 
#                                            BEFORE:BEFORE, AFTER:AFTER},
#                  ET_FLAG_CONSE_SENT: {IS_INCLUDED:IS_INCLUDED, INCLUDES:INCLUDES,
#                     NORELATION:NORELATION},
#                  ET_FLAG_WITH_DCT:{IS_INCLUDED:IS_INCLUDED, AFTER:AFTER, 
#                                     INCLUDES:INCLUDES, NORELATION:NORELATION}
#                     }