import pg8000
import datetime
from typing import Optional, List, Dict


def do_transaction_command_manage(config_db, sql_string, return_serial=False):
    connection = pg8000.connect(**config_db)
    cursor = connection.cursor()
    cursor.execute(sql_string)
    result = cursor.fetchall() if return_serial else []
    connection.commit()
    connection.close()
    return result
  
  
def get_dict_data_from_database(
    config_db: Dict, 
    sql_string: str, 
    return_serial: Optional[bool] = True
    )-> List[Dict]:
    """
    Parameters:
     - config_db: the configuration of database.
     - sql_string: structured query language.
     - return_serial: will return data via sql_string or not.
    Returns:
     - result: return a list consist of dictionary format data.
    Example:
    >>> config_db = {
    >>>     "database": "db_name",
    >>>     "user": "user_name",
    >>>     "password": "password",
    >>>     "host": "127.0.0.1",
    >>>     "port": "9453"
    >>> }
    >>> sql_string = "SELECT * FROM { table_name } WHERE { condition };"
    >>> data = get_dict_data(config_db, sql_string)
    """
    
    connection = pg8000.connect(**config_db)
    cursor = connection.cursor()
    cursor.execute(sql_string)
    result = cursor.fetchall() if return_serial else []
    connection.commit()
    connection.close()
    
    columns = [desc[0] for desc in cursor.description]
    result = [dict(zip(columns, row)) for row in result]
    return result
    
def get_array_data_from_database(
    config_db: Dict, 
    sql_string: str, 
    return_serial: Optional[bool] = True
    )-> List[Dict]:

    connection = pg8000.connect(**config_db)
    cursor = connection.cursor()
    cursor.execute(sql_string)
    result = cursor.fetchone() if return_serial else []
    connection.commit()
    connection.close()
    return result[0]

def list_to_pg_array_str(input_list: List):
    if input_list != None:
        element_str = "','".join(input_list)
        array_str = f"ARRAY['{element_str}']"
    else:
        array_str = "NULL"
    return array_str

def sql_inj_check(msg):
    msg = msg.upper()
    black_words = ["TABLE", "SELECT", "DATABASE", "DELETE", "UPDATE", "DROP", "CREATE", "EXISTS", "IF", ";"]
    for _word in black_words:
        msg = msg.replace(_word, "")
    return msg