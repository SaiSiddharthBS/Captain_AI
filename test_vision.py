from src.vision import VisionEngine
import time
ve = VisionEngine('moondream')
t1=time.time()
res=ve.look_at_screen()
print('Time:', time.time()-t1)
print(res)
