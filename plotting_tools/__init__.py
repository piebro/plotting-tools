from .pre_process import main as pre_process_main
from .plot import main as plot_main
import subprocess
from os import path

def pre_process():
  pre_process_main()

def plot():
  plot_main()

def edit_axidraw_config():
  dir_path = path.dirname(path.realpath(__file__))
  subprocess.run(["gedit", dir_path+"/axidraw_config.py"])

def edit_pre_process_config():
  dir_path = path.dirname(path.realpath(__file__))
  subprocess.run(["gedit", dir_path+"/pre_process_config.py"])
