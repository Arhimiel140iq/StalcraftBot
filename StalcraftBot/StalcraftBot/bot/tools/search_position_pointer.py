import pyautogui
import time


while True:

    x, y = pyautogui.position()
    positionStr = f'X: {x}, Y: {y}'
    print(positionStr, end='\r')  
    time.sleep(0.1)  


    