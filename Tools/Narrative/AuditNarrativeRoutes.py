import unreal,json,math
P=unreal.Paths.project_dir();W=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();actors=list(unreal.GameplayStatics.get_all_actors_of_class(W,unreal.Actor));report=json.load(open(P+'Saved/NarrativeBuildReport.json'));out=[]
ward=next(a for a in actors if a.get_actor_label()=='PROP_Scene01_Wardrobe');old=ward.get_actor_location();ward.set_actor_location(unreal.Vector(320,-470,0),False,False)
ignore=[a for a in actors if a.get_actor_label().startswith(('SET_','NPC_','NAR_Master_','CINE_','PROP_House_Living_Sofa_ThreeSeat')) or a.get_editor_property('hidden')]
for r in report['routes']:
 for i,(a,b) in enumerate(zip(r['points'],r['points'][1:])):
  h=unreal.SystemLibrary.capsule_trace_single(W,unreal.Vector(a[0],a[1],95),unreal.Vector(b[0],b[1],95),50,88,unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignore,unreal.DrawDebugTrace.NONE,True);v=h.to_tuple() if h else None
  if v and v[0]:out.append({'beat':r['beat'],'actor':r['actor'],'segment':i,'from':a,'to':b,'hit':v[9].get_actor_label() if v[9] else None})
json.dump({'issues':out,'checked_segments':sum(len(r['points'])-1 for r in report['routes'])},open(P+'Saved/NarrativeRouteAudit.json','w'),indent=2)

ward.set_actor_location(old,False,False)
