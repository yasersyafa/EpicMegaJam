import unreal,json
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world();pc=unreal.GameplayStatics.get_player_controller(w,0);pawn=unreal.GameplayStatics.get_player_pawn(w,0)
pts=[(-1045,2280,100),(-1045,1760,100),(-1045,1450,100),(-1045,710,100),(-750,710,100),(-350,710,100),(-90,710,100),(-90,400,100),(-200,300,100),(-280,270,100)]
r=[]
for a,b in zip(pts,pts[1:]):
 h=unreal.SystemLibrary.capsule_trace_single(w,unreal.Vector(*a),unreal.Vector(*b),34.,88.,unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[pawn],unreal.DrawDebugTrace.NONE,True)
 t=h.to_tuple() if h else None;r.append({'from':a,'to':b,'blocked':bool(t and t[0]),'actor':t[9].get_actor_label() if t and t[0] and t[9] else None})
json.dump({'segments':r,'passed':not any(x['blocked'] for x in r)},open(unreal.Paths.project_dir()+'Saved/ArrivalValidation/route.json','w'),indent=2)
