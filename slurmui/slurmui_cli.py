from slurmui import run_ui
from argparse import ArgumentParser

def slurmui_cli():
    # adding arguments later
    parser = ArgumentParser("SLURM UI")
    parser.add_argument("--debug", action='store_true')
    parser.add_argument("--cluster", type=str)
    args = parser.parse_args()
    run_ui(debug=args.debug, cluster=args.cluster)

