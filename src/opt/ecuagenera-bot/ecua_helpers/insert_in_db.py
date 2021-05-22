"""
Small helper script to add initial users in MongoDB.
Execute via `python3 -m helpers.insert_in_db` from project root

"""

import json
import os

from ecua_utils.db_utils import get_db_col

users_col = get_db_col()

print(f'There are currently {users_col.count_documents({})} documents in the collection.')

# users.json must be placed in same folder first
with open(f'{os.path.dirname(os.path.realpath(__file__))}/users.json') as f:
    data = json.load(f)

# Uncomment if you really want to import
# x = users_col.insert_many(data["users"])

print(f'There are now {users_col.count_documents({})} documents in the collection.')
