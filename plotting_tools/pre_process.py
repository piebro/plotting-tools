import argparse
import subprocess
import os.path

import xml.etree.ElementTree as ET
import re

import plotting_tools.pre_process_config as configs

PIXEL_TO_MM_MULT = 3.779527559
PAPER_SIZES_LANDSCAPE = {
    "a3":[420,297],
    "a4":[297,210],
    "a5":[210,148],
    "a6":[148,105],
    "a7":[105,74],
    "card":[149,111]
}

STYLE = 'stroke-width:{};fill:none;stroke-linejoin:round;stroke-linecap:round;stroke:#000'

def getArgs():
  parser = argparse.ArgumentParser()
  parser.add_argument("input", help="path to the input file")
  return parser.parse_args()

def get_current_transform_matrix(root):
  transformNode = list(root)[0]
  currentTransformMatrix = transformNode.attrib['transform'][7:-1].split(',')
  return list(map(float, currentTransformMatrix))

def reorder_and_clip_path_at_sides(input, output, configs):
  subprocess.run(["axicli", input,
    "--output=" + output,
    "--preview",
    "--reorder=4",
    "--rendering=1"])

  et = ET.parse(output)
  root = et.getroot()

  for child in list(root):
    if(child.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label') != '% Preview'):
      root.remove(child)
    else:
      drawingPath = list(list(child)[1])[0]
      child.attrib.pop('{http://www.inkscape.org/namespaces/inkscape}label')
      for child2 in list(child):
        child.remove(child2)
      child.append(drawingPath)


  if configs.LOG:
    print("clipped path")

  return et

def center_rescale(et, configs):
  def getSvgSize(root):
    if "viewBox" in root.attrib:
      viewBox = re.split(' |,',root.attrib["viewBox"])
      width = float(re.findall(r'(\d+(?:\.\d+)?)',viewBox[2])[0])
      height = float(re.findall(r'(\d+(?:\.\d+)?)',viewBox[3])[0])
    elif "viewbox" in root.attrib:
      viewBox = re.split(' |,',root.attrib["viewbox"])
      width = float(re.findall(r'(\d+(?:\.\d+)?)',viewBox[2])[0])
      height = float(re.findall(r'(\d+(?:\.\d+)?)',viewBox[3])[0])
    elif "width" in root.attrib and "height" in root.attrib:
      width =  float(re.findall(r'(\d+(?:\.\d+)?)',root.attrib["width"])[0])
      height =  float(re.findall(r'(\d+(?:\.\d+)?)',root.attrib["height"])[0])
    else:
      raise ValueError("invalid svg. No viewBox or width and height in svg file")
    return [width, height]

  def calcScaleAndOffset(svg_size, targetSize, configs):
    widthMult = svg_size[1]/svg_size[0]

    newTargetSize = [targetSize[0]-2*configs.SVG_BORDER,
    targetSize[1]-2*configs.SVG_BORDER]

    if newTargetSize[0] * widthMult <= newTargetSize[1]:
      newWidth = configs.SVG_SCALE * targetSize[0]
      newHeight = newWidth * widthMult
    else:
      newHeight = configs.SVG_SCALE * newTargetSize[1]
      newWidth = newHeight / widthMult

    offsetX = (newTargetSize[0] - newWidth) / 2 + configs.SVG_BORDER
    offsetY = (newTargetSize[1] - newHeight) / 2 + configs.SVG_BORDER

    scale = newWidth/svg_size[0] * PIXEL_TO_MM_MULT
    offset = [offsetX * PIXEL_TO_MM_MULT, offsetY * PIXEL_TO_MM_MULT]
    return [scale,offset]

  root = et.getroot()
  svg_size = getSvgSize(root)
  targetSize = PAPER_SIZES_LANDSCAPE[configs.PAPER_FORMAT]
  if configs.SVG_AS_PORTRAIT:
    targetSize = [targetSize[1],targetSize[0]]
  [scale, offset] = calcScaleAndOffset(svg_size, targetSize, configs)


  currentTransformMatrix = get_current_transform_matrix(root)

  currentTransformMatrix[0] *= scale
  currentTransformMatrix[3] *= scale
  currentTransformMatrix[4] += offset[0]
  currentTransformMatrix[5] += offset[1] 

  list(root)[0].attrib['transform'] = 'matrix({},{},{},{},{},{})'.format(*currentTransformMatrix)

  root.attrib["viewBox"] = "0 0 {} {}".format(targetSize[0]*PIXEL_TO_MM_MULT, targetSize[1]*PIXEL_TO_MM_MULT)
  root.attrib["width"] = "{}mm".format(targetSize[0])
  root.attrib["height"] = "{}mm".format(targetSize[1])

  if(configs.LOG):
    print("centered")
    print("scaled to {}mm x {}mm".format(targetSize[0], targetSize[1]))

  return [targetSize[0]*PIXEL_TO_MM_MULT, targetSize[1]*PIXEL_TO_MM_MULT, offset[0], offset[1]]

def unify_line_length(et, configs):
  root = et.getroot()
  pathNode = list(list(root)[0])[0]

  stroke_width = configs.STROKE_WIDTH/get_current_transform_matrix(root)[0]/PIXEL_TO_MM_MULT
  pathNode.attrib['style'] = STYLE.format(stroke_width)

def add_text(et, svg_size, input, configs):
  def getText_alphabet1(text, endX, y, height):
    def getPath(charArray, l, x, y):
      path = ""
      for line in charArray:
        path += "M{},{}".format(line[0]*l+x, -line[1]*l+y)
        for i in range(2, len(line), 2):
          path += "L{},{}".format(line[i]*l+x, -line[i+1]*l+y)
      return path

    baseLength = height/7
    alphabet = {
      "?": [[0,7,3,7,4,6,3,5,1,5,0,4,1,3,4,3],[2,0,2,1,3,1,3,0,2,0]],
      ".": [[1,0,1,1,2,1,2,0,1,0]],
      "-": [[1,3,3,3]],
      "=": [[1,4,3,4],[1,2,3,2]],
      "/": [[0,0,1,1,1,2,2,3,2,4,3,5,3,6,4,7]],
      "0": [[0,1,0,5,1,6,3,6,4,5,4,1,3,0,1,0,0,1]],
      "1": [[0,4,2,6,2,0],[1,0,3,0]],
      "2": [[0,5,1,6,3,6,4,5,4,4,0,0,4,0]],
      "3": [[0,5,1,6,3,6,4,5,4,4,3,3,1,3],[3,3,4,2,4,1,3,0,1,0,0,1]],
      "4": [[3,0,3,6,0,3,4,3]],
      "5": [[4,6,0,6,0,4,3,4,4,3,4,1,3,0,0,0]],
      "6": [[4,5,3,6,1,6,0,5,0,1,1,0,3,0,4,1,4,2,3,3,1,3,0,2]],
      "7": [[0,6,4,6,3,5,3,4,2,3,2,2,1,1,1,0]],
      "8": [[3,3,4,4,4,5,3,6,1,6,0,5,0,4,1,3,3,3,4,2,4,1,3,0,1,0,0,1,0,2,1,3]],
      "9": [[4,4,3,3,1,3,0,4,0,5,1,6,3,6,4,5,4,1,3,0,1,0,0,1]],
      "a": [[4,1,3,0,1,0,0,1,0,3,1,4,3,4,4,3,4,0]],
      "b": [[0,7,0,0],[0,3,1,4,3,4,4,3,4,1,3,0,0,0]],
      "c": [[4,3,3,4,1,4,0,3,0,1,1,0,3,0,4,1]],
      "d": [[4,7,4,0],[4,3,3,4,1,4,0,3,0,1,1,0,3,0,4,1]],
      "e": [[0,2,4,2,4,3,3,4,1,4,0,3,0,1,1,0,3,0,4,1]],
      "f": [[4,7,3,7,2,6,2,0],[1,3,3,3]],
      "g": [[0,-2,1,-3,3,-3,4,-2,4,3,4,3,3,4,1,4,0,3,0,1,1,0,3,0,4,1]],
      "h": [[0,7,0,0],[0,3,1,4,3,4,4,3,4,0]],
      "i": [[2,6,2,5],[1,4,2,4,2,0],[1,0,3,0]],
      "j": [[2,6,2,5],[1,4,2,4,2,0,1,-1]],
      "k": [[1,7,1,0],[1,2,2,2,4,4],[2,2,4,0]],
      "l": [[1,7,2,7,2,0],[1,0,3,0]],
      "m": [[0,4,0,0],[0,3,1,4,2,3,2,0],[2,3,3,4,4,3,4,0]],
      "n": [[0,0,0,4],[0,3,1,4,3,4,4,3,4,0]],
      "o": [[1,0,0,1,0,3,1,4,3,4,4,3,4,1,3,0,1,0]],
      "p": [[0,-3,0,1,0,3,1,4,3,4,4,3,4,1,3,0,0,0]],
      "q": [[4,0,1,0,0,1,0,3,1,4,3,4,4,3,4,-3]],
      "r": [[1,0,1,4],[1,3,2,4,3,4]],
      "s": [[4,4,1,4,0,3,1,2,3,2,4,1,3,0,0,0]],
      "t": [[2,7,2,1,3,0,4,1],[1,3,3,3]],
      "u": [[0,4,0,1,1,0,3,0,4,1],[4,4,4,0]],
      "v": [[0,4,0,3,1,2,1,1,2,0,3,1,3,2,4,3,4,4]],
      "w": [[0,4,0,1,1,0,2,1,2,4],[2,1,3,0,4,1,4,4]],
      "x": [[0,4,4,0],[0,0,4,4]],
      "y": [[0,4,0,1,1,0,3,0,4,1],[4,4,4,-2,3,-3,1,-3,0,-2]],
      "z": [[0,4,4,4,0,0,4,0],[1,2,3,2]],
    }
    
    path = ""
    for i in range(len(text)):
      x = endX-(5*len(text)-i*(5))*baseLength
      if text[i] in alphabet:
        path += getPath(alphabet[text[i]], baseLength, x, y)
    return path

  text = configs.CUSTOM_TEXT
  if(configs.ADD_FILENAME_AS_TEXT):
    text += os.path.splitext(os.path.basename(input))[0]

  root = et.getroot()
  style = STYLE.format(configs.STROKE_WIDTH/PIXEL_TO_MM_MULT)
  path = getText_alphabet1(text, svg_size[0]*(1-configs.TEXT_BORDER), svg_size[1]*(1-configs.TEXT_BORDER), svg_size[0]*configs.TEXT_SIZE)
  root.append(ET.Element("path", d=path, style=style))
  
  if(configs.LOG):
    print("added Text: " + text)

def add_background(et, configs):
  root = et.getroot()
  bgElement = ET.Element("rect", x="-100000", y="-100000", width="1000000", height="1000000", style="fill:rgb(255,255,255)") 
  root.insert(0,bgElement)

  if configs.LOG:
    print("added white background")

def getTimePrediction(output, configs):
  proc = subprocess.run(["axicli", output,
    "--preview",
    "--report_time"], encoding='utf-8', stderr=subprocess.PIPE)

  print(proc.stderr.split('\n')[0])

def surround_with_box(et, svg_size, configs):
  root = et.getroot()
  print(svg_size)
  box = ET.Element("rect", x=str(svg_size[2]), y=str(svg_size[3]), width=str(svg_size[0]-2*svg_size[2]), height=str(svg_size[1]-2*svg_size[3]), style="stroke:rgb(0,0,0);stroke-width:" + str(configs.STROKE_WIDTH/PIXEL_TO_MM_MULT) + ";fill:none") 
  root.insert(0,box)
  if configs.LOG:
    print("added surround box")

def main():
  args = getArgs()
  output = os.path.dirname(args.input) + "/plotter-ready_" + os.path.basename(args.input)

  et = reorder_and_clip_path_at_sides(args.input, output, configs)

  svg_size = center_rescale(et, configs)

  unify_line_length(et, configs)

  if(configs.SURROUND_WITH_BOX):
    surround_with_box(et, svg_size, configs)
  
  if(configs.ADD_TEXT):
    add_text(et, svg_size, args.input, configs)

  add_background(et, configs)

  et.write(output)
  print("saved to: ", output)

  getTimePrediction(output, configs)




if __name__ == "__main__":
    main()