# -*- coding: utf-8 -*-
#
# A simple memory cache library
# Author: Craig Russell <craig@craig-russell.co.uk>
#
# =============
# Sources from: https://gist.github.com/craig552uk/dc93ae5578a59a338d96
import time

class Cache(object):

    _cache_ = {}
    VALUE   = 0
    EXPIRES = 1

    @classmethod
    def get(cls, key):
        """Get the value from the cache stored with 'key' if it exists"""
        try:
            if cls._cache_[key][cls.EXPIRES] > time.time():
                return cls._cache_[key][cls.VALUE]
            else:
                del cls._cache_[key] # Delete the item if it has expired
                return None
        except KeyError:
            return None

    @classmethod
    def set(cls, key, value, duration=3600):
        """Store/overwite a value in the cache with 'key' and an optional duration (seconds)"""
        try:
            expires = time.time() + duration
        except TypeError:
            raise TypeError("Duration must be numeric")

        cls._cache_[key] = (value, expires)
        return cls.get(key)

    @classmethod
    def clean(cls):
        """Remove all expired items from the cache"""
        for key in cls._cache_.keys():
            cls.get(key) # Attempting to fetch an expired item deletes it


    @classmethod
    def purge(cls):
        """Remove all items from the cache"""
        cls._cache_ = {}