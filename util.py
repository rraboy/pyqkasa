
import time

def is_true(val):
    return True if val == "true" or val == "yes" or val == "on" or val == "1" else False

def is_false(val):
    return True if val == "false" or val == "no" or val == "off" or val == "0" else False

def current_milli_time():
    return round(time.time() * 1000)
