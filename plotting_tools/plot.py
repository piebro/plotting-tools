import subprocess
from os import path
import argparse
import tempfile
from time import sleep
import re

def getArgs():
  parser = argparse.ArgumentParser()
  parser.add_argument("input", help="path to the input file")
  return parser.parse_args()

def preview(input_path, config_path):
  f = tempfile.NamedTemporaryFile()
  output_path = f.name  + ".svg"
  
  proc = subprocess.run([
    "axicli",
    input_path,
    "--config=" + config_path,
    "--preview",
    "--report_time",
    "--output_file=" + output_path
  ], encoding='utf-8', stderr=subprocess.PIPE)

  est_time_str = proc.stderr.split('\n')[0]

  print(est_time_str)
  
  subprocess.Popen([
    "eog", output_path
  ])

  m = re.search('(\\d\\d):(\\d\\d)|(\\d):(\\d\\d):(\\d\\d)', est_time_str)

  if(m.group(1) == None):
    seconds = int(m.group(3))*60*60 + int(m.group(4))*60 + int(m.group(5))
  else:
    seconds = int(m.group(1))*60+int(m.group(2))
  return seconds
  


def plot(input_path, config_path, secondes):
  print("plot")
  #preview time, run timer, plot with timer

  p = subprocess.Popen([
    "axicli",
    input_path,
    "--config=" + config_path
  ])
  
  progressBar(secondes)
  p.communicate()


def plotter_off():
  subprocess.run(["axicli","--mode=align"])

def plotter_toggle():
  subprocess.run(["axicli","--mode=toggle"])


def progressBar(secondes):
  # Print iterations progress
  def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
      print()

  # Initial call to print 0% progress
  printProgressBar(0, secondes*10, prefix = 'Progress:', suffix = 'Complete', length = 50)
  for i in range(secondes*10):
    sleep(0.1)
    # Update Progress Bar
    printProgressBar(i + 1, secondes*10, prefix = 'Progress:', suffix = 'Complete', length = 50)


def main():
  args = getArgs()
  dir_path = path.dirname(path.realpath(__file__))
 
  config_path = dir_path + "/axidraw_config.py"

  secondes = preview(args.input, config_path)

  print("Do you want to start plotting?")
  cmd = input("press y (yes), n (no), o (plotter off), t (toggle plotter pen)\n")

  if(cmd == "y"):
    plot(args.input, config_path, secondes)
    plotter_off()
  elif(cmd == "o"):
    plotter_off()
  elif(cmd == "t"):
    plotter_toggle()


  

  print("finished plotting")

if __name__ == "__main__":
    main()