"""Scene 01 dialogue manifest. Audio remains unassigned for later import."""
GROUPS={
 'Opening':[
  ('Opening_01','MAYA','People say a camera captures the truth.',5),
  ('Opening_02','MAYA',"I don't think that's true.",4),
  ('Opening_03','MAYA','It only captures what someone chooses to show you.',6),
  ('Opening_04','MAYA',"And I think... that's what makes films so interesting.",6)],
 'CrewIntro':[
  ('Intro_Crew_01','CREW A',"Morning, Director. We're almost ready in the front room.",4.51),
  ('Intro_Crew_02','SURYA',"Good. How's the set looking?",3.09),
  ('Intro_Crew_03','CREW A',"A few pieces still need placing. Thought you'd want the final say.",5.59)],
 'MayaIntro':[
  ('Intro_Maya_01','MAYA','Morning, Mr. Surya.',2.5),
  ('Intro_Maya_02','SURYA','Morning, Maya. Ready for your first scene?',3.8),
  ('Intro_Maya_03','MAYA',"As ready as I'll ever be.",3.44),
  ('Intro_Maya_04','SURYA',"Don't worry about getting everything perfect. We'll work through it.",4.87),
  ('Intro_Maya_05','MAYA',"That's reassuring. I've been going over the script all morning.",4.87),
  ('Intro_Maya_06','SURYA',"You'll be fine. Let's take a look at the room.",4.87)],
 'TakeEntry':[('Take_Entry_01','LARAS (MAYA)',"It's strange being back.",3.3)],
 'TakeWalk':[('Take_Walk_01','LARAS (MAYA)',"I thought I'd remember every corner of this place.",4.5)],
 'TakeClue':[
  ('Take_Clue_01','LARAS (MAYA)','Wait...',1.8),
  ('Take_Clue_02','LARAS (MAYA)',"Wasn't there a doorway here?",3)],
 'TakePerfect':[
  ('Take_Perfect_01','LARAS (MAYA)',"I could've sworn there was a door here.",3.5),
  ('Take_Perfect_02','LARAS (MAYA)',"Maybe I'm remembering it wrong.",3)],
 'FailureSofa':[
  ('Fail_Sofa_01','MAYA','Sorry... should I come around this side instead?',4.5),
  ('Fail_Sofa_02','SURYA (INTERNAL)',"The blocking's a bit cramped. I should cut and clear some space.",5)],
 'FailureWardrobe':[
  ('Fail_Wardrobe_01','MAYA',"I'm not quite sure what I'm meant to notice.",4.5),
  ('Fail_Wardrobe_02','SURYA (INTERNAL)',"The composition isn't helping her find the moment.",4)],
 'CutSofa':[('Cut_Sofa_01','SURYA',"CUT! Let's open up that walkway. We'll go again.",4)],
 'CutWardrobe':[('Cut_Wardrobe_01','SURYA',"CUT! Let's give her a clearer view of the wall. We'll go again.",4.5)],
 'CutEarly':[('Cut_Early_01','SURYA',"CUT! Let's reset and go again.",2.8)],
 'Aftermath':[
  ('Aftermath_01','SURYA','CUT! Lovely. That felt very natural.',3.5),
  ('Aftermath_02','MAYA',"Thanks. I wasn't sure if I held that last pause too long.",4.5),
  ('Aftermath_03','SURYA','No, it worked. Gave the moment a bit of space.',4),
  ('Aftermath_04','MAYA','Great. One down, then.',2.5),
  ('Aftermath_05','SURYA','One down.',1.8)],
 'CrewTransition':[
  ('Transition_01','CREW A','Shall we clear the room?',2.5),
  ('Transition_02','SURYA',"Yes, please. Let's move on to the kitchen.",3.5),
  ('Transition_03','CREW B',"I'll bring the lighting kit through.",3)],
}

def rows():
    result=[]
    for group,lines in GROUPS.items():
        for i,(line,speaker,text,duration) in enumerate(lines):
            result.append(dict(LineID=line,Speaker=speaker,Subtitle=text,Sound='None',FallbackSeconds=str(duration),NextLine=lines[i+1][0] if i+1<len(lines) else '',Spatial='False' if group=='Opening' or speaker.startswith('SURYA') else 'True',Group=group))
    return result
