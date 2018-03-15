from nltk import ParentedTree
from parsed_term import *
import logging

logger = logging.getLogger('svm_training')
class Tree:
    def __init__ (self, tree_repr ):
        self.tree = ParentedTree.parse(tree_repr)
    
    def get_highest_event (self, list_of_event_pos):
        """
        Method to get the main event in a list of event
        position in a sentence.
        When there is a tie, the first one is chosen.
        Actually 'cause event only account for one token,
        we could use leaf_treeposition to get the distance from root
        to that leaf.
        Parameters:
            - list_of_event_pos: a list of positions of event
                in the sentence, which are a list of integer
                indicate the extend of event in the sentence,
                assumed that event is one token extend.
        Return:
            - the index of event in the list_of_event_pos
        
        """
        highest = None
        highest_distance = 100
        
        part_of_speech_list = self.tree.pos()
        for i in xrange(len(list_of_event_pos)):
            event_pos = list_of_event_pos[i]
            try:
                distance = len(self.tree.leaf_treeposition(event_pos))
            
                if distance < highest_distance:
                     highest_distance = distance
                     highest = i
                elif distance == highest_distance:
                    try:
                        highest_POS = part_of_speech_list[list_of_event_pos[highest]][1]
                        current_POS = part_of_speech_list[list_of_event_pos[i]][1]
                        """
                        If the current event is actually a verb, it should 
                        replace the highest event with the same high
                        """
                        if highest_POS[0] != 'V' and current_POS[0] == 'V':
                            highest_distance = distance
                            highest = i
                    except Exception:
                        logger.warn("Problem in comparing part of speech of two \
                                    highest event candidate")
            except IndexError as ie:
                logger.warn("Index error")
                logger.info('Event pos %d' %event_pos)
                logger.info('Tree length %d' %len(self.tree.leaves()))
                logger.info(str(self.tree))
        return highest
    
    def get_tree_distance (self, index_1_beg, index_1_end,
                           index_2_beg, index_2_end ):
        """
        Get the distance in the syntactic tree
        between two extends.
        The particular purpose of the method in the task
        is to find the distance between two events or an event
        and the time in a sentence.
        """
        tempo_2_beg = index_2_beg
        tempo_2_end = index_2_end
        if index_1_beg >= index_2_end:
            index_2_beg = index_1_beg
            index_2_end = index_1_end
            index_1_beg = tempo_2_beg
            index_1_end = tempo_2_end
        
        if  index_1_end - index_1_beg > 1:
            lca_1 = self.tree[self.tree.\
                              treeposition_spanning_leaves( index_1_beg, index_1_end )]
        else:
            lca_1 = self.tree[self.tree.\
                              treeposition_spanning_leaves( index_1_beg, index_1_end )[:-1]]

        if  index_2_end - index_2_beg > 1:
            lca_2 = self.tree[self.tree.\
                              treeposition_spanning_leaves( index_2_beg, index_2_end )]
        else:
            lca_2 = self.tree[self.tree.\
                              treeposition_spanning_leaves( index_2_beg, index_2_end )[:-1]]

        if  index_2_end - index_1_beg > 1:
            lca = self.tree[self.tree.\
                            treeposition_spanning_leaves( index_1_beg, index_2_end )]
        else:
            lca = self.tree[self.tree.\
                            treeposition_spanning_leaves( index_1_beg, index_2_end )[:-1]]

        distance = max(len(lca_1.treeposition()) - len(lca.treeposition()),
                   len(lca_2.treeposition()) - len(lca.treeposition())
                )
        
        return distance
    
    def get_pruned_tree_path (self, index_1_beg, index_1_end,
                           index_2_beg, index_2_end, in_between_children = False ):
        """
        Get the path in the syntactic tree
        between two extends.
        The particular purpose of the method in the task
        is to find the minimum tree that connects between two events,
        removing the POS and LEMMA of single token entity,
        removing internal structure of multiple token entity
        (consider the multiple token entity as one node in the tree)
        removing branches and leaves in between two entities
        Parameters:
            - index_1_beg, index_1_end: begin and end of the first entity,
                index_1_end is exclusive
            - index_2_beg, index_2_end: begin and end of the second entity,
                index_2_end is exclusive
            - in_between_children: a flag whether to include the first level of children
                of the common ancestor of two entities
        """
        tempo_2_beg = index_2_beg
        tempo_2_end = index_2_end
        if index_1_beg >= index_2_end:
            index_2_beg = index_1_beg
            index_2_end = index_1_end
            index_1_beg = tempo_2_beg
            index_1_end = tempo_2_end
        
        if  index_1_end - index_1_beg > 1:
            lca_1_index = self.tree.treeposition_spanning_leaves( index_1_beg, index_1_end )
        else:
            lca_1_index = self.tree.treeposition_spanning_leaves( index_1_beg, index_1_end )[:-1]

        if  index_2_end - index_2_beg > 1:
            lca_2_index = self.tree.treeposition_spanning_leaves( index_2_beg, index_2_end )
        else:
            lca_2_index = self.tree.treeposition_spanning_leaves( index_2_beg, index_2_end )[:-1]
            
        if  index_2_end - index_1_beg > 1:
            lca_index = self.tree.treeposition_spanning_leaves( index_1_beg, index_2_end )
        else:
            lca_index = self.tree.treeposition_spanning_leaves( index_1_beg, index_2_end )[:-1]
            
        lca = self.tree[lca_index]
        new_tree = ParentedTree('(' + lca.node + ')')

        #Point to the root
        # Branch of the first entity
        current_pointer = new_tree
        tempo_lca = lca
#         try:
        for i in xrange(len(lca_index), len(lca_1_index)):
            tempo_lca = tempo_lca[lca_1_index[i]]
            if not (type(tempo_lca) == str or type(tempo_lca) == unicode):
                current_pointer.insert(0, ParentedTree('('+tempo_lca.node +')'))
                current_pointer = current_pointer[0]

        current_pointer = new_tree
        #Insert the first level of children of lca
        if len(lca_index) < len(lca_1_index) and len(lca_index) < len(lca_2_index):
            if in_between_children:
                for i in xrange(lca_1_index[len(lca_index)] + 1, lca_2_index[len(lca_index)]):
                    current_pointer.insert(i, ParentedTree('('+lca[i].node +')'))

        #Point to the root
        # Branch of the second entity
        current_pointer = new_tree
        tempo_lca = lca
        first_time = True
        for i in xrange(len(lca_index), len(lca_2_index)):
            tempo_lca = tempo_lca[lca_2_index[i]]
            if not (type(tempo_lca) == str or type(tempo_lca) == unicode):
                if first_time:
                    if not in_between_children:
                        children_index_of_2nd_branch = 1
                    else:
                        """
                        Don't really need to check lca_2_index[len(lca_index)]
                        'cause if it come to this point, the length constraint
                        is already satisfied
                        However, it's necessary to check lca_1_index[len(lca_index)]
                        """
                        if len(lca_index) < len(lca_1_index):
                            children_index_of_2nd_branch = lca_2_index[len(lca_index)]\
                                                           - lca_1_index[len(lca_index)]
                        else:
                            """
                            No left child, no in_between_children
                            """
                            children_index_of_2nd_branch = 0
                    current_pointer.insert(children_index_of_2nd_branch,
                                           ParentedTree('('+tempo_lca.node +')'))
                    current_pointer = current_pointer[children_index_of_2nd_branch]
                    first_time = False
                else:
                    current_pointer.insert(0, ParentedTree('('+tempo_lca.node +')'))
                    current_pointer = current_pointer[0]
        return new_tree
#         except IndexError:
#             print lca_1_index
#             print lca_2_index
#             print lca_index
#             print index_1_beg
#             print index_1_end
#             print index_2_beg
#             print index_2_end
#             print self.tree[lca_1_index]
#             print self.tree[lca_2_index]
#             print lca
            
    
    @classmethod
    def prune_tree( cls, tree, begin_index, end_index ):
        """
        Prune the tree that include the begin_index and the end_index
        so that it doesn't include leaves outside of the range limited
        by begin_index and end_index
        """
        
        begin_path = tree.leaf_treeposition(begin_index)
        end_path = tree.leaf_treeposition(end_index)

        current_node = tree[begin_path[:-1]]
        end_node = tree[end_path[:-1]]
        
        new_tree = ParentedTree('(' + tree.node + ')')
        ## Initialize new tree
        l = []
        current_new = new_tree
        current_old = tree
        for i in xrange(len(begin_path)-1):
            if type(current_old[begin_path[i]]) != str:
                current_new.insert(0, ParentedTree('('+current_old[begin_path[i]].node +')'))
                current_new = current_new[0]
                current_old = current_old[begin_path[i]]
        
        while current_old != end_node:
            if not (type(current_old[0]) == str or type(current_old[0]) == unicode):
                current_old = current_old[0]
                current_new.insert( 0, ParentedTree('('+current_old.node +')'))
                current_new = current_new[0]
            else:
                current_new.insert(0, current_old[0])
                while len(current_old.parent()) == current_old.parent_index() + 1:
                    current_old = current_old.parent()
                    current_new = current_new.parent()

                current_old = current_old.parent()[current_old.parent_index() + 1]
                current_new.parent().insert( current_new.parent_index() + 1,
                                                 ParentedTree('('+current_old.node +')'))
                
                current_new = current_new.parent()[current_new.parent_index() + 1]
        current_new.insert(0, current_old[0])
#         print current_new
        return new_tree

    def parse_tree_for_sub_component(self, index_1_beg, index_1_end,
                                     index_2_beg, index_2_end, flag_string):
        """
        Get the subtree given the extends of two entities
        at the beginning and the end of the subtree.
            - flag_string: either utilities.parsed_term.SUBTREE_PT
                            or utilities.parsed_term.SUBTREE_MCT
                            or utilities.parsed_term.SUBTREE_CSPT
            SUBTREE_PT: is the pruned_tree that enclose two entities
                    and no more token outside of these entities
            SUBTREE_MCT: the complete tree without pruning that enclose
                    two entities
            SUBTREE_CSPT: CSPT means PT extending with the 1st left sibling of 
                    the node of entity 1 and the 1st right sibling of the node 
                    of entity 2
        """
        
        tempo_2_beg = index_2_beg
        tempo_2_end = index_2_end
        if index_1_beg >= index_2_end:
            index_2_beg = index_1_beg
            index_2_end = index_1_end
            index_1_beg = tempo_2_beg
            index_1_end = tempo_2_end

        ##  Path-enclosed Tree (PT)
        if flag_string == SUBTREE_PT:
            if  index_2_end - index_1_beg > 1:
                subtree_pos = self.tree.treeposition_spanning_leaves( index_1_beg, index_2_end )
                lca = self.tree[subtree_pos]
                no_of_leaves = self.number_of_leaves_before(subtree_pos)
                return Tree.prune_tree(lca, index_1_beg - no_of_leaves, index_2_end - 1 - no_of_leaves)
            else:
                return self.tree[self.tree.treeposition_spanning_leaves( index_1_beg, index_2_end )[:-1]]
        
        ## Minimum Complete Tree (MCT)
        if flag_string == SUBTREE_MCT:
            if  index_2_end - index_1_beg > 1:
                lca = self.tree[self.tree.treeposition_spanning_leaves( index_1_beg, index_2_end )]
            else:
                lca = self.tree[self.tree.treeposition_spanning_leaves( index_1_beg, index_2_end )[:-1]]
            return lca

        ## Context-Sensitive Path Tree (CSPT)
        if flag_string == SUBTREE_CSPT:
            if index_1_beg > 0:
                index_1_beg -= 1
            if index_2_end < len(self.tree.leaves()) - 1:
                index_2_end += 1
            subtree_pos = self.tree.treeposition_spanning_leaves( index_1_beg, index_2_end )
            lca = self.tree[subtree_pos]
            no_of_leaves = self.number_of_leaves_before(subtree_pos)
            return Tree.prune_tree(lca, index_1_beg - no_of_leaves, index_2_end - 1 - no_of_leaves)
        
        ## Highly-pruned Path Tree (HPPT)
        if flag_string == SUBTREE_HPPT:
            # Get a single path tree that connect 
            # the two entities 
            return self.get_pruned_tree_path(index_1_beg, index_1_end,
                                     index_2_beg, index_2_end, True)

    def number_of_leaves_before( self, sub_position ):
        begin_index = 0
        end_index = len(self.tree.leaves()) - 1

        if sub_position < self.tree.leaf_treeposition(0):
            return 0

        while ( begin_index + 1 < end_index ):
            middle_index = int((end_index + begin_index)/2) 
            middle_pos = self.tree.leaf_treeposition(middle_index)
            if middle_pos < sub_position:
                begin_index = middle_index
            else:
                end_index = middle_index
            
        return end_index


def test_tree():
    tree_string = "(ROOT\
                      (S\
                        (NP\
                          (NNP NAIROBI)\
                          (, ,)\
                          (NNP Kenya)\
                          (-LRB- -LRB-)\
                          (NNP AP)\
                          (-RRB- -RRB-))\
                        (ADVP (RB _))\
                        (PRN\
                          (S\
                            (NP (JJ Suspected) (NNS bombs))\
                            (VP\
                              (VBD exploded)\
                              (PP (IN outside) (NP (DT the) (NNP U.S.) (NNS embassies)))\
                              (PP\
                                (IN in)\
                                (NP\
                                  (DT the)\
                                  (ADJP (JJ Kenyan) (CC and) (JJ Tanzanian))\
                                  (NNS capitals)))\
                              (NP-TMP (NNP Friday))\
                              (, ,)\
                              (S\
                                (VP\
                                  (VBG killing)\
                                  (NP (NP (NNS dozens)) (PP (IN of) (NP (NNS people))))))))\
                          (, ,))\
                        (NP (NNS witnesses))\
                        (VP (VBD said))\
                        (. .)))"
    tree = Tree(tree_string)
    tree.get_pruned_tree_path(9,10,22,23)  
