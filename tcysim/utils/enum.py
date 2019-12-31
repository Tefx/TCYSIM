from enum import auto

class Exum:
    def __new__(cls):
        cls.__last_value = 0
