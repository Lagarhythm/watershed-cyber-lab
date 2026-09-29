"""Build the guided mission notebook; the teaching interface is one custom widget."""
from pathlib import Path
import nbformat as n
root=Path(__file__).resolve().parent
nb=n.v4.new_notebook(cells=[n.v4.new_code_cell('from mission import GuidedMission\nGuidedMission()',metadata={'jupyter':{'source_hidden':True},'tags':['hide-input']})],metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'},'title':'Watershed · Guided Mission'})
n.write(nb,root/'Guided_Mission.ipynb')
