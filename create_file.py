str_ = "ABCDEF"

with open("bigfile.txt", 'w') as f:
        f.write(str_*2000)