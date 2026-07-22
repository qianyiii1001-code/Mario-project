from ctypes import windll
import time

driver = windll.LoadLibrary('inpoutx64.dll')
PORT = 0x3FF8  # 不行就换成 0x3FF0

for i in range(5):
    driver.Out32(PORT, 255)
    time.sleep(0.5)
    driver.Out32(PORT, 0)
    time.sleep(0.5)