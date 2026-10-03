import os, sys, io
import M5
from M5 import *
import requests2
import time


localTime = None
localDate = None
image0 = None
http_req = None
file_0 = None
sleep_mins = 60


x = None
fileName = None

# Describe this function...
def addZero(x):
  global fileName, localTime, localDate, image0, http_req, file_0
  if (int(x)) < 10:
    x = (str('0') + str(x))
  return x


def setup():
  global localTime, localDate, image0, http_req, file_0, x, fileName

  M5.begin()
  Widgets.setRotation(2)
  Widgets.fillScreen(0xffffff)
  localDate = Widgets.Label("...", 0, 936, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu24)
  # originally date widget was at x25
  image0 = Widgets.Image("res/img/default.png", 0, 0, scale_x=1, scale_y=1)

def refresh_image():
  img_url = 'http://10.0.3.253:5000/'
  fileName = 'img.png'
  http_req = requests2.get(img_url, headers={'Content-Type': 'application/json'})
  print((str(((str('Status: ') + str((http_req.status_code))))) + str(((str(' ') + str(((str('Content-Length: ') + str(((http_req.headers)['Content-Length']))))))))))
  if (http_req.status_code) == 200:
    file_0 = open('/flash/' + str((str('res/img/') + str(fileName))), 'wb+')
    file_0.write(http_req.content)
    file_0.close()
    image0.setImage("res/img/" + str(fileName))
    

def loop():
  global sleep_mins, localTime, localDate, image0, http_req, file_0, x, fileName
  batt_level = Power.getBatteryLevel()
  refresh_image()
  
  localDate.setText(" %d%% " % (batt_level,))
  time.sleep(20)
  Power.timerSleep(60*sleep_mins)


if __name__ == '__main__':
  try:
    setup()
    while True:
      loop()
  except (Exception, KeyboardInterrupt) as e:
    try:
      Display.setFont(M5.Lcd.FONTS.DejaVu24)
      from utility import print_error_msg
      print_error_msg(e)
      Display.print(f"FOO WILL SLEEP IN ")
      for remaining in range(0,21):
        Display.print(f"... {20-remaining}")
        time.sleep(1)
      Display.print(f"\n\nSLEEPING FOR {sleep_mins}min\n")
      Power.timerSleep(60*sleep_mins)
    except ImportError:
      print("please update to latest firmware")

