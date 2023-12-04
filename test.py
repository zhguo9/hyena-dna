import re
x = "CGCGATGATCACCAC57DS"
print(x[-6:])
match = re.search(r"\d+",x)
if match:
    position = int(match.group(0))
else:
    position = 1
print(position)