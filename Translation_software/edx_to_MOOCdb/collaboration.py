from helperclasses import * 
import pickle
import os

class CollaborationManager(object):

    def __init__(self, moocdb):
        self.collaborations = moocdb.collaborations
    
    def update_collaboration_table(self,event):
        event_type = event['event_type']
        event_class = event.__class__.__name__
        
        # Only ForumInteraction
        # events are of interest here.
        if event_class not in ['ForumInteraction']:
            return
        
        self.collaborations.store(event.get_collaboration_row())
        
    def serialize(self, pretty_print_to=''):
        pass
#        self.problem_hierarchy.serialize(pretty_print_to)
        
        
    

    

        

