
import sys

sys.path.append("/home/lichzhang/code/JKTW/server/tools")
from commonlib import *



init_aip()
res = get_car_number("test1.jpg")

number_list = [] 
for num in res["words_result"]:
   number_list.append(num["number"])

print (number_list)



