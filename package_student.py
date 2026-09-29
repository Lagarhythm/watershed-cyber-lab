"""Package runtime and evidence without instructor answers or saved outputs."""
from pathlib import Path
import json
import zipfile
ROOT=Path(__file__).parent
QUICKSTART='''# Watershed — student simulation
Keep this folder together. You need Python 3.10+ (Linux or macOS). From this folder run:

    ./start.sh

The first run installs everything (about a minute); later runs start right away. Then open http://127.0.0.1:8866 in your browser (the VM desktop browser, or your own browser after forwarding port 8866 through SSH). The Guided Mission starts automatically and shows no Python: follow each step's instructions, read what you learned, answer the quick check, and click Next. For the free-play dashboard, run `./start.sh --full`. Press Ctrl+C in the terminal to stop.

Manual setup (Windows, or if start.sh fails):

    python -m venv .venv
    .venv\\Scripts\\activate            (Linux/macOS: source .venv/bin/activate)
    python -m pip install -r requirements.txt
    python launch.py

No Internet is needed after installation. All actions affect a fictional model, never real hosts. The free-play dashboard saves your decision journal in this browser on this origin; choose Resume saved attempt after reopening, and reset between learners on a shared browser profile. Download report exports JSON for discussion. Local assessment is formative, not a secure exam. The original Cybersecurity_Interactive_Lab.ipynb is an optional code-oriented companion.
'''
def package(destination=None):
    dest=Path(destination) if destination else ROOT.parent/'cybersecurity_showcase_student.zip'
    notebook=json.loads((ROOT/'Cybersecurity_Interactive_Lab.ipynb').read_text())
    for cell in notebook['cells']:
        if cell['cell_type']=='code': cell['outputs']=[]; cell['execution_count']=None
    notebook['metadata'].pop('widgets',None)
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        prefix='cybersecurity_showcase/'
        z.writestr(prefix+'Cybersecurity_Interactive_Lab.ipynb',json.dumps(notebook,indent=1))
        z.writestr(prefix+'README.md',QUICKSTART)
        simulation=json.loads((ROOT/'Watershed_Simulation.ipynb').read_text())
        for cell in simulation['cells']:
            if cell['cell_type']=='code': cell['outputs']=[]; cell['execution_count']=None
        simulation['metadata'].pop('widgets',None)
        z.writestr(prefix+'Watershed_Simulation.ipynb',json.dumps(simulation,indent=1))
        z.write(ROOT/'Guided_Mission.ipynb',prefix+'Guided_Mission.ipynb')
        for path in [*sorted((ROOT/'mission').glob('*.py')), *sorted((ROOT/'mission').glob('*.js')), *sorted((ROOT/'mission').glob('*.css')), *sorted((ROOT/'simulator').glob('*.py')), *sorted((ROOT/'simulator').glob('*.js')), *sorted((ROOT/'simulator').glob('*.css')), ROOT/'lab.py',ROOT/'requirements.txt',ROOT/'launch.py',ROOT/'start.sh',*sorted((ROOT/'jupyter').rglob('*.json')),*sorted((ROOT/'jupyter').rglob('*.j2')),*sorted((ROOT/'data').glob('*')), *sorted((ROOT/'assets').glob('*'))]: z.write(path,prefix+str(path.relative_to(ROOT)))
    return dest
if __name__=='__main__': print(package())
