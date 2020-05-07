import os
import struct


fat_path = "FAT/"            # название папки
sector_size = 0x200         # размер сектора (512)
sector_per_cluster = 0x4    # количество секторов в кластере (4)
reserved_sectors = 0x0001   # количество зарезервированных секторов (1)
sector_per_fat = 0x0001     # количество секторов зарезервированных под таблицу (1)
root_entries = 0x20         # количество секторов зарезервированных под корневой каталог (32)

def make_start_files():
    os.mkdir(fat_path) 
    for file_name in range(0xff5):   
        hex_name = '0x%08x'%file_name
        f = open(fat_path + "/" + hex_name, 'w')
        f.close()
    hex_name = fat_path + '0x%08x'%1
    with open(hex_name, 'a') as f:
        f.write("0xffff\n")
        for i in range(0, int(0x200)//2 - 1):
            f.write("0x0000\n")

def parse_file_params(s):
    d = dict()
    d["name"], d["type"], d["attribute"], d["head_cluster"], d["tail_cluster"], d["is_exists"] = s.split()

    return d


def read_sector(secror):
    hex_name = fat_path + '0x%08x'%secror
    with open(hex_name, 'r') as f:
        lines = f.read().splitlines()
    temp = []
    for l in lines:
        temp.append(parse_file_params(l))
    return temp

def check_cluster_bad(cluster):
    flag_bad = False
    bias = reserved_sectors + 2*sector_per_fat + root_entries + (cluster-1)*sector_per_cluster
    for s in range(sector_per_cluster):
        hex_name = '0x%08x'%(bias + s)
        if not(os.path.exists(fat_path + hex_name)):
            flag_bad = True
            add_bad_cluster(cluster)
            
            print("Bad sector:", hex_name)
    return flag_bad

def search_new_cluster(new_clusters):
    hex_name_fat = fat_path + '0x%08x'%reserved_sectors
    with open(hex_name_fat, 'r') as f:
        lines = f.read().splitlines()
    
    for index, i in enumerate(lines):
        if i == "0x0000":
            flag = True
            for cluster in new_clusters:
                if index == cluster:
                    flag = False
                    break
                elif check_cluster_bad(index):
                    lines[index] = "0xfff7"
                    flag = False
                    break
                        

            if flag:
                return index
    return 0
    
def update_table_fat(new_clusters):
    hex_name_fat = fat_path + '0x%08x'%reserved_sectors
    with open(hex_name_fat, 'r') as f:
        lines = f.read().splitlines()
    
    temp = []
    for l in lines:
        temp.append(int(l, 16))

    for i,cluster in enumerate(new_clusters):
        if cluster != new_clusters[-1]:
            temp[cluster] = new_clusters[i+1]
        else:
            temp[cluster] = 0xffff

    with open(hex_name_fat, 'w') as f:
        for i in temp:
            f.write('0x%04x'%i+'\n')

def check_file_in_dirrectory(filename, path):
    if path == "/" or path == "":
        pass
    else:
        pass

def add_file():
    print("Enter path to file: ", end="")
    path = input()

    if not(os.path.exists(path)):
        return
    
    name = os.path.basename(path)
    index = name.index('.')
    print()

    bias_sectors = reserved_sectors + 2*sector_per_fat
    for sector in range(root_entries):
        if len(read_sector(bias_sectors + sector)) < 32:
            bias_sectors += sector
            break
    
    size_file = os.path.getsize(path)
    if (size_file % sector_size == 0):
        need_sectors = size_file // sector_size
    else:
        need_sectors = size_file // sector_size + 1

    if (need_sectors % sector_per_cluster == 0):
        need_clusters = need_sectors // sector_per_cluster
    else:
        need_clusters = need_sectors // sector_per_cluster + 1

    new_clusters = []
    for i in range(need_clusters):
        new_clusters.append(search_new_cluster(new_clusters))
    
    update_table_fat(new_clusters) 

    hex_name = fat_path + '0x%08x'%bias_sectors
    with open(hex_name, 'a') as f:
        f.write(name[:index] + " " + name[index+1:] + " " + "r"+" " + str(new_clusters[0]) + " " + "0" + " " + "1"+ "\n")

    bias_sectors += root_entries

    temp_f = []
    with open(path, 'r') as f:
        for i in range(need_sectors):
            temp_f.append(f.read(sector_size))
     
    for i, part in enumerate(temp_f):
        sector_temp = i % 4
        cluster_temp = i // 4
        hex_pos = bias_sectors + (new_clusters[cluster_temp]-1)*sector_per_cluster + sector_temp
        with open(fat_path+ '0x%08x'%hex_pos, 'w') as f:
            print('0x%08x'%hex_pos, "written")
            f.write(part)
        if sector_temp == 3:
            print()
    print()

def add_bad_cluster(num):
    hex_name_fat = fat_path + '0x%08x'%reserved_sectors
    with open(hex_name_fat, 'r') as f:
        lines = f.read().splitlines()
    
    temp = []
    for l in lines:
        temp.append(int(l, 16))

    temp[num] = 0xfff7

    with open(hex_name_fat, 'w') as f:
        for i in temp:
            f.write('0x%04x'%i+'\n')

def duplicate_fat_table():
    hex_name_fat = fat_path + '0x%08x'%reserved_sectors
    with open(hex_name_fat, 'r') as f:
        lines = f.read().splitlines()
    hex_name_fat = fat_path + '0x%08x'%(reserved_sectors + sector_per_fat)
    with open(hex_name_fat, 'w') as f:
        for line in lines:
            f.write(line+"\n")

def print_files():
    files = []
    for index in range(0x20):
        hex_name_fat = fat_path + '0x%08x'%(reserved_sectors + 2*sector_per_fat + index)
        with open(hex_name_fat, 'r') as f:
            lines = f.read().splitlines()
        for line in lines:
            file_ = parse_file_params(line)
            if file_:
                files.append(file_)
    print()
    for f in files:
        if f["is_exists"]:
            print("head_cluster="+f["head_cluster"]+"\t\t"+f["name"]+"."+f["type"])
    print()


def del_file(head_cluster, table):
    cursor = head_cluster
    while table[cursor] != 0xffff:
        new_cursor = table[cursor]
        table[cursor] = 0x0000
        cursor = new_cursor
    table[cursor] = 0x0000

    hex_name_fat = fat_path + '0x%08x'%reserved_sectors
    with open(hex_name_fat, 'w') as f:
        for i in table:
            f.write('0x%04x'%i+'\n')

def check_file_system():
    files = []
    for index in range(0x20):
        hex_name_fat = fat_path + '0x%08x'%(reserved_sectors + 2*sector_per_fat + index)
        with open(hex_name_fat, 'r') as f:
            lines = f.read().splitlines()
        for line in lines:
            file_ = parse_file_params(line)
            if file_:
                files.append(file_)
    
    hex_name_fat = fat_path + '0x%08x'%reserved_sectors
    with open(hex_name_fat, 'r') as f:
        lines = f.read().splitlines()
    
    temp = []
    for l in lines:
        temp.append(int(l, 16))
    
    bad_sectors = []

    for f in files:
        flag = False
        need_to_check = []
        cursor = int(f["head_cluster"])
        while cursor != 0xffff:
            bias_sectors = reserved_sectors + 2*sector_per_fat + root_entries + (cursor-1)*sector_per_cluster
            for sector_temp in range(sector_per_cluster):
                hex_pos = bias_sectors + sector_temp
                need_to_check.append('0x%08x'%hex_pos)
            cursor = temp[cursor]
        for n in need_to_check:
            if not(os.path.exists(fat_path + n)):
                flag = True
                bad_sectors.append(n)
        print(bad_sectors)
        if flag:
            del_file(int(f["head_cluster"]), temp)
            for i in bad_sectors:
                b_s = int(i, 16)
                b_s -= (reserved_sectors + 2*sector_per_fat + root_entries)
                add_bad_cluster(b_s//sector_per_cluster + 1)

            hex_name_fat = fat_path + '0x%08x'%(reserved_sectors + 2*sector_per_fat)
            with open(hex_name_fat, 'r') as f_:
                lines = f_.read().splitlines()
            files_temp = []
            for line in lines:
                file_ = parse_file_params(line)
                if file_:
                    files_temp.append(file_)
            with open(hex_name_fat, 'w') as f_:
                for ff in files_temp:
                    if f["head_cluster"] != ff["head_cluster"]:
                        f_.write(ff["name"]+" "+ff["type"]+" "+ff["attribute"]+" "+ff["head_cluster"]+" "+ff["tail_cluster"]+" "+ff["is_exists"]+"\n")


def menu():
    print("[1] Add file")
    print("[2] Add bad cluster")
    print("[3] Print files")
    print("[4] Check filesystem")

    print("\n[0] Exit\n")
    print(" > ", end="")
    command = input()
    if command == "0":
        print("Exit")
        exit()
    elif command == "1":
        add_file()
    elif command == "2":
        print("Enter number of cluster: ", end="")
        num_cluster = int(input())
        add_bad_cluster(num_cluster)
    elif command == "3":
        print_files()
    elif command == "4":
        check_file_system()
    else:
        print("Incorrect command. Try again.\n")
    duplicate_fat_table()



def main():
    if not(os.path.exists(fat_path)) :
        make_start_files()
        duplicate_fat_table()

    while(True):
        menu()

main()