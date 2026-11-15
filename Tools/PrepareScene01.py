from Scene01Editor import *
print(stage('PrepareScene01.py'))
for path in [CONTROLLER,PLAYER]:
    s=call('read_blueprint_graph_summary',path=path,graphName='EventGraph')
    (OUT/(cls(path)+'_events.json')).write_text(json.dumps(s,indent=2))
    print(path,[(n['id'],n['title']) for n in s['nodes']])
