"""Require the L02 lamp's spotlight to face the concealed doorway at ACTION."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph

P = '/Game/Game/Blueprints/Film/BP_FilmSceneManager'
variables = call('list_variables', path=P)['variables']
if not any(v['name'] == 'L02SpotlightBeam' for v in variables):
    call('add_variable', path=P, variableName='L02SpotlightBeam', type='object:SpotLight', category='Scene 02')

s = call('read_blueprint_graph_summary', path=P, graphName='EvaluateSetup')
if not any(n['title'] == 'Get L02SpotlightBeam' for n in s['nodes']):
    g = Graph(P, 'EvaluateSetup')
    beam = g.get('L02SpotlightBeam')
    direction = g.fn('beamForward', 'Actor', 'GetActorForwardVector')
    g.wire(beam, direction + '.self')
    dot = g.fn('doorDot', 'KismetMathLibrary', 'Dot_VectorVector', B='(X=-0.326,Y=0.941,Z=-0.09)')
    g.wire(direction + '.ReturnValue', dot + '.A')
    aimed = g.fn('isAimed', 'KismetMathLibrary', 'Greater_DoubleDouble', B='0.86')
    g.wire(dot + '.ReturnValue', aimed + '.A')
    valid = g.fn('beamValid', 'KismetSystemLibrary', 'IsValid')
    g.wire(beam, valid + '.Object')
    valid_aim = g.fn('validAim', 'KismetMathLibrary', 'BooleanAND')
    g.wire(valid + '.ReturnValue', valid_aim + '.A')
    g.wire(aimed + '.ReturnValue', valid_aim + '.B')
    is_lit = g.fn('isLitFlag', 'KismetMathLibrary', 'EqualEqual_NameName', B='bClueLit')
    g.wire('E26B0F4B.FlagName_2_031A26F5454CA0E1000B4A8F1CA56A1D', is_lit + '.A')
    other_flag = g.fn('otherFlag', 'KismetMathLibrary', 'Not_PreBool')
    g.wire(is_lit + '.ReturnValue', other_flag + '.A')
    pass_or_aim = g.fn('passOrAim', 'KismetMathLibrary', 'BooleanOR')
    g.wire(other_flag + '.ReturnValue', pass_or_aim + '.A')
    g.wire(valid_aim + '.ReturnValue', pass_or_aim + '.B')
    final = g.fn('finalLit', 'KismetMathLibrary', 'BooleanAND')
    g.wire('57DB3B47.ReturnValue', final + '.A')
    g.wire(pass_or_aim + '.ReturnValue', final + '.B')
    g.wire(final + '.ReturnValue', 'DB8A4120.Value')
    g.build()

print(call('compile_blueprint', path=P))
print(call('save_blueprint', path=P))
