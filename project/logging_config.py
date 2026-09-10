import logging.config
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def rotating_file(filename, level):
    return{
        "class" : "logging.handlers.RotatingFileHandler",
        "filename" : os.path.join(LOG_DIR, filename),
        "maxBytes" : 5* 1024 * 1024,
        "backupCount" : 10,
        "formatter" : "default",
        "level" : level,
        "encoding" : "utf-8"}

LOGGING_CONFIG = {
    "version" : 1,
    "disable_existing_loggers" : False,

    "formatters":{
        "default" : {
            "format" : "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "datefmt" : "%y-%m-%d %H:%M:%S" }
        },
    "handlers":{
        "console":{
            "class" : "logging.StreamHandler",
            "formatter" : "default",
            "level" : "DEBUG"} , 
        "app_file": rotating_file("app.log", "INFO"),
        "error_file" : rotating_file("error.log", "ERROR"),
        "auth_file" : rotating_file("auth.log", "INFO"),
        "catalog_file" : rotating_file("catalog.log", "INFO"),
        "orders_file" : rotating_file("orders.log", "INFO")
    },
    "root":{
        "handlers": ["console", "app_file", "error_file"],
        "level" : "DEBUG"
    },
    "loggers":{
        "project.oauth2":{
            "handlers" : ["auth_file"],
            "propagate" : True,
            "level" : "INFO"},
        "project.routers.auth":{
            "handlers" : ["auth_file"],
            "propagate" : True,
            "level" : "INFO"},
        "project.routers.categories":{
            "handlers" : ["catalog_file"],
            "propagate" : True,
            "level" : "INFO"},
        "project.routers.services":{
            "handlers" : ["catalog_file"],
            "propagate" : True,
            "level" : "INFO"},
        "project.routers.ServicePlans":{
            "handlers" : ["catalog_file"],
            "propagate" : True,
            "level" : "INFO"},
        "project.routers.orders":{
            "handlers" : ["orders_file"],
            "propagate" : True,
            "level" : "INFO"},
        "project.routers.transactions":{
            "handlers" : ["orders_file"],
            "propagate" : True,
            "level" : "INFO"},
        "project.routers.subscriptions":{
            "handlers" : ["orders_file"],
            "propagate" : True,
            "level" : "INFO"},
        "uvicorn": {"level":"INFO"},
        "sqlalchemy.engine":{"level":"WARNING"}
    }
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)