"""Launch the student app with the bundled, CDN-free Voilà template."""
import argparse
import os
import sys
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description='Launch the Watershed student app on localhost.')
    parser.add_argument('--port',type=int,default=8866)
    parser.add_argument('--full',action='store_true',help='open the free-play Incident Command dashboard instead of the guided mission')
    args=parser.parse_args()
    notebook='Watershed_Simulation.ipynb' if args.full else 'Guided_Mission.ipynb'
    root=Path(__file__).resolve().parent
    os.environ['JUPYTER_PATH']=str(root/'jupyter')+(os.pathsep+os.environ['JUPYTER_PATH'] if os.environ.get('JUPYTER_PATH') else '')
    os.chdir(root)
    # Open a browser only where there is a desktop; over plain SSH, a terminal browser could take over the session.
    desktop=sys.platform in ('darwin','win32') or os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
    print(f'\n  Watershed is starting. Open http://127.0.0.1:{args.port} in your browser. Press Ctrl+C here to stop.\n',flush=True)
    from voila.app import Voila
    Voila.launch_instance(argv=[str(root/notebook),*([] if desktop else ['--no-browser']),f'--port={args.port}','--Voila.ip=127.0.0.1','--template=watershed'])

if __name__=='__main__': main()
