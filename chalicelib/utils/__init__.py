from chalicelib.components import do_transaction_pg
from chalicelib.components import setting

def create_relevant_tables() -> dict:
    sql = f"""
        CREATE SCHEMA IF NOT EXISTS community;
        CREATE TABLE IF NOT EXISTS community.community_info
        (
            serial_no integer NOT NULL,
            commu_no character varying COLLATE pg_catalog."default",
            name character varying COLLATE pg_catalog."default" NOT NULL,
            device_no character varying COLLATE pg_catalog."default",
            district character varying COLLATE pg_catalog."default",
            lat double precision,
            lon double precision,
            x_mean double precision,
            x_max double precision,
            x_min double precision,
            y_mean double precision,
            y_max double precision,
            y_min double precision,
            last_api_status boolean,
            api_status boolean,
            last_alive_3h boolean,
            alive_3h boolean,
            last_warning_status jsonb,
            warning_status jsonb,
            geom geometry,
            last_record_time timestamp without time zone,
            api_status_note character varying COLLATE pg_catalog."default",
            source_api character varying COLLATE pg_catalog."default",
            CONSTRAINT community_info_pkey PRIMARY KEY (serial_no, name)
        );
    """
    do_transaction_pg.do_transaction_command_manage(config_db=setting.config_db, sql_string=sql)
    return {
        "status": True,
        "detail": "created relevant tables already"
    }

create_relevant_tables()