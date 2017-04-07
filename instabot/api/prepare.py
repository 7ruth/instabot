#!/usr/bin/env python
import os
import sys
import getpass
import warnings
from ..user import User

from .. import config


def add_credentials(username=None, password=None):
    if username is None or password is None:
        print("Enter your login: ")
        username = str(sys.stdin.readline().strip())
        print("Enter your password: (you won't see it)")
        password = getpass.getpass()
    User(username, password).save()


def choose_user_dialogue():
    while True:
        print("Which account do you want to use? (Type number)")
        all_users = User.get_all_users()
        for ind, login in enumerate(all_users):
            print("%d: %s" % (ind + 1, login))
        print("%d: %s" % (0, "add another account."))
        try:
            ind = int(sys.stdin.readline())
            if ind == 0:
                add_credentials()
                continue
            if ind - 1 in list(range(len(all_users))):
                return User.load(all_users[ind - 1])
        except:
            print("Wrong input. I need the number of account to use.")


def get_credentials(username=None, password=None):
    if username is not None:
        if username in User.get_all_users():
            usr = User.load(username)
            if password is not None:
                usr.password = password
            return usr
        elif password is not None:
            usr = User(username, password)
            usr.save()
            return usr
        else:
            warnings.warn(
                "User not found in base. Please provide credentials.")
    return choose_user_dialogue()


def delete_credentials(username):
    User.delete(username)


if __name__ == "__main__":
    check_secret()
