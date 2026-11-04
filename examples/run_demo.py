"""Run the demonstration on synthetic data and print the report."""
from qa_open.cli import run_demo

print(run_demo(seed=0, months=24))
