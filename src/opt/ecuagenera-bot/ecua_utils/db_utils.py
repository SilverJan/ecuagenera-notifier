import pymongo
from .util import reload_config_yml


# Returns `db` collection instance
def get_db_col():
    config = reload_config_yml()
    # get user list from DB
    client = pymongo.MongoClient(
        f"mongodb+srv://{config['mongo_user']}:{config['mongo_pw']}@{config['mongo_url']}")
    db = client["db"]
    users_col = db["users"]
    return users_col


# Returns all users in `db` collection
# More information about filters can be found in https://docs.mongodb.com/manual/tutorial/project-fields-from-query-results
def get_db_users(filter={}, projection=None) -> list:
    users_col = get_db_col()
    return list(users_col.find(filter, projection))


# Returns a list of a given field (e.g. `username`) of all users in the collection
def get_db_users_field(field, filter={}, projection=None):
    users = get_db_users(filter, projection)
    list = []
    for user in users:
        list.append(user[field])
    return list


def set_user_config(user: dict, config: str, value: any) -> bool:
    col = get_db_col()
    result = col.update_one({'_id': user['_id']}, {
                            '$set': {f"config.{config}": value}})
    return result.acknowledged

def set_user_expiry_date(user: dict, value: str) -> bool:
    col = get_db_col()
    result = col.update_one({'_id': user['_id']}, {
                            '$set': {"expiry_date": value}})
    return result.acknowledged

class Config:
    AUTO_CHECKOUT = "auto_checkout"
    WISHLIST = "wishlist"
    PLAN = "plan"
