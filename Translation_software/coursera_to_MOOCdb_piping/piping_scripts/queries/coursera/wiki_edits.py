from ...utilities import db, moocdb_utils
from datetime import datetime
from common import *

def GetWikiEdits(vars):
    # DB connections
    # --------------
    s = vars['source']
    general_db_selector = db.Selector(s['host'], s['user'], s['password'], s['port'], s['general_db'])
    
    wiki_edit_ctid = moocdb_utils.GetCollaborationTypeMap(vars)['wiki_edit']
    
    gen_anon = vars['general_anon_col_name']
    
    items = []
    q = "SELECT * FROM wiki_revisions JOIN `{0}`.hash_mapping USING ({1})".format(vars['source']['hash_mapping_db'], gen_anon)
    if vars['options']['debug']:
        q += " WHERE wiki_revisions.{} IN ({})".format(gen_anon, ",".join(vars['hash_map']['qls_general']))
    wiki_revisions = general_db_selector.query(q)
    
    vars["logger"].Log(vars, "Counts: Read {} wiki edits from source".format(len(wiki_revisions)))
    
    xi = 0
    for x in wiki_revisions:
        items.append({
            'original_id': 'wiki_edit_' + str(xi),
            'user_original_id': vars['hash_map']['map_general'][x[gen_anon]],
            'collaboration_parent_original_id': None,
            'resource_original_id': x['page_id'],
            'collaboration_child_number': None,
            'collaboration_timestamp': datetime.fromtimestamp(x['timestamp']),
            'collaboration_type_id': wiki_edit_ctid,
            'collaboration_content': None,
        })
        xi += 1
        
    return items