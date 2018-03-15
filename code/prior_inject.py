"""
This file is a modification of 
incorporate_tlink.py, adopting code from
compare_performance.py, the purpose is to
inject result from result file into the no_tlink files,
with modification of result based on prior obtained from
event-pair.
The algorithm is as following:
- Calculate P ( lemma_pair | label ) with label = [BEFORE, AFTER, *SIMULTANEOUS]
    Could be calculated directly by the number of pairs in the 
    narrative scheme, or by doing a smoothing step.
    P ( lemma_pair | SIMULTANEOUS ) is set == 1/2N where N is the total 
    number of pair line in the corpus. (2 because lemma pair could be
    swapped).
    
- Calculate P ( result_vector | label ) with label = [BEFORE, AFTER, SIMULTANEOUS]
    Get result_vector* corresponding to that label (remove the 
        dimension comparing two other labels).
    Detail of implementation:
    For example:
        Consider:
        result_vector: {"('SIMULTANEOUS', 'AFTER')": 1.0958849, 
                        "('AFTER', 'BEFORE')": -2.1010391, 
                        "('SIMULTANEOUS', 'BEFORE')": -1.7459796}
        result_vector* = {('AFTER', 'BEFORE'): -2.1010391, 
                        ('SIMULTANEOUS', 'BEFORE'): -1.7459796}
        label = BEFORE
        
        P ( result_vector | label ) = P(  -2.1010391 | classifier = ('AFTER', 'BEFORE'), 
                                                        label = BEFORE )
                                    x P(  -1.7459796 | classifier = ('SIMULTANEOUS', 'BEFORE'), 
                                                        label = BEFORE )
                                    
        where P( (Label1, Label2): value | Label1 ) is calculated by histogram bin method
            = 
            Percent of training samples (traing the classifier for Label1
             vs Label2) that fell into the same bin with value
             that has Label1.
        
- Calculate P ( label | lemma_pair, result_vector ) ~ P ( result_vector | label )
                                                x P ( lemma_pair | label )
    following Naive Bayes method, given that we assume lemma pair and 
    result_vectors are independent features.
- Inject back the TLINK with the result label received from the aforementioned
    method.
"""