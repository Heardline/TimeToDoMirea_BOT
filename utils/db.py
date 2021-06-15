import pandas as pd,os
import utils.time_lessons as time_lesson
import psycopg2
import utils.scrap_schedul as updater
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
try:
        # Подключение к существующей базе данных
        connection = psycopg2.connect(user="postgres",
                                    # пароль, который указали при установке PostgreSQL
                                    password="k686999",
                                    host="127.0.0.1",
                                    port="5432",
                                    database="Schedul")
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()
except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)

def setup_notify(boolen,telegram_id):
    cursor.execute("Update students set notify = " + boolen + " WHERE telegram_id =  %s",telegram_id)
    if cursor.fetchone():
        return True
    else:
        return False

def check_group(group):
    cursor.execute("SELECT id FROM groups WHERE name = '" + group + "';")
    if cursor.fetchone():
        print(cursor.fetchone())
        return True
    else:
        return False
        

def check_user(telegram_id):
    cursor.execute("SELECT grp FROM students WHERE telegram_id = '" + str(telegram_id) + "';")
    if cursor.fetchone():
        print(cursor.fetchone())
        return True
    else:
        return False
    
def update_data():
    updater.download_xlsx()
    remove_data()
    import_from_xlsx()

def import_group(group,univercity):
    try:
        create_table_query = '''INSERT INTO groups ( name, univercity) VALUES (%s, %s);'''
        cursor.execute(create_table_query,(group,univercity))
        connection.commit()
        return True

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
        return False


def add_user(group,telegram_id):
    try:
        create_table_query = f"INSERT INTO students (grp,telegram_id, notify) VALUES ({group},{telegram_id}, True);"
        cursor.execute(create_table_query)
        connection.commit()
        print(f"Пользователь {telegram_id} успешно зарегестирован в PostgreSQL")
        return True
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL add_user", error)
        return False

def get_group(telegram_id):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT grp FROM groups WHERE telegram_id = {telegram_id};")
        id_group = cursor.fetchone()
        create_table_query = '''SELECT name FROM groups WHERE id = %s;'''
        cursor.execute(create_table_query,id_group)
        connection.commit()
        print(f"Пользователь {telegram_id} успешно создан в PostgreSQL")
        return cursor.fetchone()

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL get_group", error)
        return False

def init_db():
    try:
        cursor = connection.cursor()
        create_table_query = ''''''
        cursor.execute(create_table_query)
        connection.commit()
        print("Таблица успешно создана в PostgreSQL")

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)

def import_lesson(name,teacher,room,type,time, group):
    try:
        cursor = connection.cursor()
        create_table_query = '''INSERT INTO lessons (subj, prep,room,type,tstart,day,odd,grp) VALUES (%s, %s,%s,%s,%s,%s,%s,%s);'''
        if (time %2) == 1:
            odd = 0
        else: odd = 1
        cursor.execute(create_table_query,(str(name),str(teacher),str(room),str(type),time%12, time//12,odd, str(group)))
        #print(name,teacher,room,type,time%12," ", time//12, " ",odd)
        connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL import_lesson", error, name, teacher,room)

def remove_data():
    try:
        cursor = connection.cursor()
        create_table_query = '''DELETE from lessons;'''
        cursor.execute(create_table_query)
        #print(name,teacher,room,type,time%12," ", time//12, " ",odd)
        connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL remove_data ", error)

def import_from_xlsx():
    excel_names = os.listdir("data/xlsx/")
    for names in excel_names:
        data_df = pd.read_excel("data/xlsx/"+names,header=1)
        for index in data_df.columns:
            if "-" in str(index):
                import_group(str(index),names.split(r'_')[0])
                for time in range(1,75):
                    if str(data_df.iloc[time,data_df.columns.get_loc(index)]) == "nan":
                        pass
                    else:
                        import_lesson(data_df.iloc[time,data_df.columns.get_loc(index)],data_df.iloc[time,data_df.columns.get_loc(index)+2],data_df.iloc[time,data_df.columns.get_loc(index)+3],data_df.iloc[time,data_df.columns.get_loc(index)+1],time,index) 
        #print(data_df.iloc[2,data_df.columns.get_loc("ГДБО-01-20")])


#Получение данных из dataframe. time_row - код времени(в зависимости от четной и не четной недели)
def get_lesson(time_row,group,type):
    try:
        cursor = connection.cursor()
        create_table_query = f"SELECT {type} FROM lessons WHERE group = {group} and tstart = {time_row%12} and day = {time_row//12};"
        cursor.execute(create_table_query)
        #print(name,teacher,room,type,time%12," ", time//12, " ",odd)
        return cursor.fetchone()
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL get_lesson", error)