from typing import Optional, Dict, Any, List, Tuple
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import AKI_MONGO_HOST
from datetime import datetime, timedelta, timezone

if not AKI_MONGO_HOST:
    raise RuntimeError("AKI_MONGO_HOST env var is missing")

my_client = MongoClient(
    host=AKI_MONGO_HOST,
    server_api=ServerApi("1"),
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=20000,
    retryWrites=True,
    retryReads=True,
)
# NOTE: to verify connectivity at startup, call my_client.admin.command("ping") in a try/except — do NOT ping unconditionally at import time.
my_db = my_client["aki-db"] #selecting the database


def addUser(user_id: int, first_name: str, last_name: str, user_name: str) -> None:
    """
    Adding the User to the database. If user already present in the database,
    it will check for any changes in the user_name, first_name, last_name and will update if true.
    """
    #"Users" Collection (Table).
    my_col = my_db["users"]
    #Finding if the user_id of the user is in the collection (Table), if found, assigning it to user variable.
    user = my_col.find_one({"user_id": user_id}) 
    #Checking if the user_id matches with the one from the Collection (Table).
    #If the user_id is not in the Collection (Table), the below statement adds the user to the Collection (Table).
    if user is None:
        my_dict = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "user_name": user_name,
        "aki_lang": "en",
        "child_mode": 1,
        "total_guess": 0,
        "correct_guess": 0,
        "wrong_guess": 0,
        "unfinished_guess": 0,
        "total_questions": 0,
    }
        my_col.insert_one(my_dict)
    elif user["user_id"] == user_id:
        updateUser(user_id, first_name, last_name, user_name)

def addgroup(chat_id:int,title:str,username:str) -> None:
    my_col = my_db["groups"]
    group = my_col.find_one({"chat_id":chat_id})
    
    if group is None:
        my_dict = {
            "chat_id":chat_id,
            "title":title,
            "username":username,
        }
        my_col.insert_one(my_dict) 
    elif group["chat_id"] == chat_id:
        updategroup(chat_id,title,username)
    


def add_last_msg_id(user_id:int,last_msg_id:int,chat_id:int,current_msg_id:int) -> None:
    my_col = my_db["last_msg_ids"]
    data = my_col.find_one({"user_id":user_id})
    
    if data is None:
        my_dict = {
            "user_id":user_id,
            "last_msg_id":last_msg_id,
            "chat_id":chat_id,
            "current_msg_id":current_msg_id
        }
        my_col.insert_one(my_dict)
    elif data["user_id"] == user_id:
        update_last_msg_id(user_id,last_msg_id,chat_id,current_msg_id)


def update_last_msg_id(user_id:int,last_msg_id:int,chat_id:int,current_msg_id:int) -> None:
    my_col = my_db["last_msg_ids"]
    to_update = {
        "last_msg_id":last_msg_id,
        "chat_id":chat_id,
        "current_msg_id":current_msg_id
        
    }
    my_col.update_one({"user_id":user_id}, {"$set":to_update})





def get_last_msg_id(user_id:int) -> Optional[int]:
    my_col = my_db["last_msg_ids"]
    data = my_col.find_one({"user_id":user_id})
    if data is None:
        return None
    else :
        return data["last_msg_id"]

def get_chat_id(user_id: int, last_msg_id: int) -> Optional[int]:
    my_col = my_db["last_msg_ids"]
    chat_info = my_col.find_one({"user_id": user_id, "last_msg_id": last_msg_id})
    if chat_info is None:
        return None
    else:
        return chat_info["chat_id"]


def get_user_id(last_msg_id: int, chat_id: int) -> Optional[int]:
    my_col = my_db["last_msg_ids"]
    user_info = my_col.find_one({"last_msg_id": last_msg_id, "chat_id": chat_id})
    if user_info is None:
        return None
    else:
        return user_info["user_id"]




def updategroup(chat_id:int,title:str,username:str) -> None:
    my_col = my_db["groups"]
    to_update = {
        "title":title,
        "username":username,
    }
    my_col.update_one({"chat_id":chat_id}, {"$set":to_update})





def totalUsers() -> int:
    my_col = my_db["users"]
    #Returns the total no.of users who has started the bot.
    return my_col.count_documents({})


def updateUser(user_id: int, first_name: str, last_name: str, user_name: str) -> None:
    """
    Update a User in the collection (Table).
    """
    my_col = my_db["users"]
    to_update = {
        "user_name": user_name,
        "first_name": first_name,
        "last_name": last_name,
    }
    my_col.update_one({"user_id": user_id}, {"$set":to_update})


def getUser(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Returns the user document (Record)
    """
    my_col = my_db["users"]
    return my_col.find_one({"user_id": user_id})


def getLanguage(user_id: int) -> str:
    """
    Gets(Returns) the Language Code of the user. (str)
    """
    my_col = my_db["users"]
    doc = my_col.find_one({"user_id": user_id})
    if doc is None:
        return "en"
    return doc.get("aki_lang", "en")


def getChildMode(user_id: int) -> int:
    """
    Get(Returns) the Child mode status of the user. (str)
    """
    my_col = my_db["users"]
    doc = my_col.find_one({"user_id": user_id})
    if doc is None:
        return 1
    return doc.get("child_mode", 1)


def getTotalGuess(user_id: int) -> int:
    
    doc = my_db["users"].find_one({"user_id": user_id})
    if doc is None:
        return 0
    return doc.get("total_guess", 0)


def getCorrectGuess(user_id: int) -> int:
    
    doc = my_db["users"].find_one({"user_id": user_id})
    if doc is None:
        return 0
    return doc.get("correct_guess", 0)



def getWrongGuess(user_id: int) -> int:
    
    doc = my_db["users"].find_one({"user_id": user_id})
    if doc is None:
        return 0
    return doc.get("wrong_guess", 0)


def getUnfinishedGuess(user_id: int) -> int:
    
    crct_wrong_guess = getCorrectGuess(user_id)+getWrongGuess(user_id)
    unfinished_guess = getTotalGuess(user_id)-crct_wrong_guess
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"unfinished_guess": unfinished_guess}})
    return my_db["users"].find_one({"user_id": user_id})["unfinished_guess"]



def getTotalQuestions(user_id: int) -> int:
    """
    
    """
    doc = my_db["users"].find_one({"user_id": user_id})
    if doc is None:
        return 0
    return doc.get("total_questions", 0)



def updateLanguage(user_id: int, lang_code: str) -> None:
    """
    Update Akinator Language for the User.
    """
    my_col = my_db["users"]
    my_col.update_one({"user_id": user_id}, {"$set": {"aki_lang": lang_code}})


def updateChildMode(user_id: int, mode: int) -> None:
    """
    Update Child Mode of the User.
    """
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"child_mode": mode}})

def updateTotalGuess(user_id: int, total_guess: int) -> None:
    
    total_guess = getTotalGuess(user_id)+total_guess
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"total_guess": total_guess}})


def updateCorrectGuess(user_id: int, correct_guess: int) -> None:
    
    correct_guess = getCorrectGuess(user_id)+correct_guess
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"correct_guess": correct_guess}})


def updateWrongGuess(user_id: int, wrong_guess: int) -> None:

    wrong_guess = getWrongGuess(user_id)+wrong_guess
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"wrong_guess": wrong_guess}})
    

def updateTotalQuestions(user_id: int, total_questions: int) -> None:
    
    total_questions = total_questions+ getTotalQuestions(user_id)
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"total_questions": total_questions}})


################# LEADERBOARD FUNCTIONS ####################

def getLead(what:str) -> List[Tuple[str, Any]]:
    lead_dict = {}
    for user in my_db['users'].find({}, {"first_name": 1, what: 1, "user_id": 1}).sort(what, -1).limit(10):
        lead_dict[user["user_id"]] = (user.get("first_name"), user.get(what))
    lead_list = sorted(lead_dict.values(), key=lambda x: x[1] if x[1] is not None else 0, reverse=True)
    return lead_list[:10]


def getAllUserIds():
    """
    Get a list of all user IDs available in the database.
    """
    my_col = my_db["users"]
    user_ids = [user["user_id"] for user in my_col.find({}, {"user_id": 1})]
    return user_ids

def getAllGroups():
    my_col = my_db["groups"]
    groups = [group["chat_id"] for group in my_col.find({}, {"chat_id": 1})]
    return groups

def gettitle(chat_id:int) -> str:
    my_col = my_db["groups"]
    return my_col.find_one({"chat_id":chat_id})["title"]

def add_user_message_data(message_id_in_admin_chat:int ,message_id_in_user_chat:int,user_id:int):
    """stores the data of the user message for replying to it later 

    Args:
        message_id_in_admin_chat (int): message id of the message which is forwarded from the user by the bot to admin 
    """
    my_col = my_db["user_chatting_data"]
    data = my_col.find_one(
        {"message_id_in_admin_chat": message_id_in_admin_chat})

    if data is None:
        my_dict = {
            "user_id": user_id,
            "message_id_in_admin_chat": message_id_in_admin_chat,
            "message_id_in_user_chat": message_id_in_user_chat,
            "created_at": datetime.now(timezone.utc),
        }
        my_col.insert_one(my_dict)
def find_user_message_data(message_id_in_admin_chat:int):
    """retrives the message_id and user id using the message_id of the forwaerded message used for replying to the message 

    Args:
        message_id_in_admin_chat (int): message id of the message which is forwarded from the user by the bot to admin 

    Returns:
        user_id: int
        message_id:int
    """
    my_col = my_db["user_chatting_data"]
    data = my_col.find_one({"message_id_in_admin_chat": message_id_in_admin_chat})

    if data is not None:
        # If data is found, return the message_id_in_user_chat and user_id
        return data["message_id_in_user_chat"], data["user_id"]
    else:
        # Return None if the message_id_in_admin_chat is not found
        return None, None
def delete_group(chat_id: int) -> None:
    """
    Deletes a group based on the provided chat_id.
    """
    my_col = my_db["groups"]
    my_col.delete_one({"chat_id": chat_id})

    
def delete_old_user_chatting_data():
    my_col = my_db["user_chatting_data"]
    # Define the time threshold for deletion (24 hours ago from the current time)
    threshold_time = datetime.now(timezone.utc) - timedelta(hours=24)

    # Find records older than the threshold time and delete them
    # (created_at preferred; timestamp fallback for legacy records)
    my_col.delete_many({"$or": [{"created_at": {"$lt": threshold_time}}, {"timestamp": {"$lt": threshold_time}}]})