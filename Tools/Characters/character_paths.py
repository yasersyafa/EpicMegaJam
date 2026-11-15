"""Character source art lives outside the Unreal project tree."""
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ART_ROOT = PROJECT_ROOT.parents[2] / 'Art' / PROJECT_ROOT.name / 'Characters'
