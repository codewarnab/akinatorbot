import akinator    
import logging
import json 
import time
from random import randint
from config import BOT_TOKEN,ADMIN_TELEGRAM_USER_ID
from akinator import Akinator
from telegram import Update ,InputMediaPhoto,error
from telegram.constants import ParseMode,ChatAction
from keyboard import (  AKI_LANG_BUTTON,
                        AKI_LEADERBOARD_KEYBOARD,
                        AKI_PLAY_KEYBOARD, 
                        AKI_WIN_BUTTON, 
                        CHILDMODE_BUTTON, 
                        START_KEYBOARD,
                        SHARE_BUTTON,
                        START_KEYBOARD_GROUP,
                        GUIDE_KEYBOARD
                            )
from telegram.ext import  (CommandHandler,
                           CallbackContext,
                           CallbackQueryHandler,
                           PicklePersistence,
                           Application,
                           CommandHandler,
                           MessageHandler,
                           filters)
from database import (
    addUser, 
    addgroup,
    getChildMode, 
    getCorrectGuess, 
    getLanguage, 
    getLead, 
    getTotalGuess, 
    getTotalQuestions, 
    getUnfinishedGuess, 
    getUser, getWrongGuess, 
    totalUsers, 
    updateChildMode, 
    updateCorrectGuess, 
    updateLanguage, 
    updateTotalGuess, 
    updateTotalQuestions, 
    updateWrongGuess,
    getAllUserIds,
    get_last_msg_id,
    get_chat_id,
    add_last_msg_id,
    update_last_msg_id,
    get_user_id,
    getAllGroups,
    gettitle,
    add_user_message_data,
    find_user_message_data
    
    )
from strings import  AKI_FIRST_QUESTION, AKI_LANG_CODE, AKI_LANG_MSG, CHILDMODE_MSG, ME_MSG, START_MSG, GROUP_LOADING_CAPTION_MSG,MENTION_USER,AKI_FIRST_IMG,AKI_DEFEATED_IMG,AKI_WIN_IMG,NONE_JPG,AKI_02,AKI_03,AKI_04,AKI_05,ERROR_IMG,PERMISSION_ISSUE,SURETY

pic_list = [AKI_02,AKI_03,AKI_04,AKI_05]



async def aki_start(update: Update, context: CallbackContext) -> None:
    # Handles the /start command.
    if update.effective_user.username == "GroupAnonymousBot":
        await update.message.reply_text(
            text="Sorry *Anoynomous* players are not allowed to play Akinator.🤫",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=GUIDE_KEYBOARD
        )
        return
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id 
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    user_name = update.effective_user.username
    type = update.effective_chat.type
    #Adding user to the database.
    addUser(user_id, first_name, last_name, user_name)
    await context.bot.send_chat_action(
        chat_id=chat_id,
        action=ChatAction.TYPING,
    )
    
    await update.message.reply_text(START_MSG.format(first_name), 
                              parse_mode=ParseMode.HTML, 
                              reply_markup=START_KEYBOARD if type == "private" else START_KEYBOARD_GROUP)
    if type !="private":
        addgroup(chat_id, update.effective_chat.title,user_name)
        
def generate_random_img():
    '''Generate random image for Akinator'''
    return pic_list[randint(0,3)]


async def aki_find(update: Update, context: CallbackContext) -> None:
    '''Find the number of user.'''
    if update.effective_user.id == ADMIN_TELEGRAM_USER_ID:
        total_users = totalUsers()
        await update.message.reply_text(f"Total Users👤 : {total_users}")



async def aki_me(update: Update, context: CallbackContext) -> None:
    #Handles the /me command
    if update.effective_user.username == "GroupAnonymousBot":
        await update.message.reply_text(
            text="Sorry *Anoynomous* players are not allowed to play Akinator.🤫",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=GUIDE_KEYBOARD
        )
        return
    user_id = update.effective_user.id
    addUser(user_id, update.effective_user.first_name, update.effective_user.last_name, update.effective_user.username)
    profile_pic =( await  update.effective_user.get_profile_photos(limit=1)).photos
    if len(profile_pic) == 0:
        profile_pic = "https://telegra.ph/file/a65ee7219e14f0d0225a9.png"
    else:
        profile_pic = profile_pic[0][1]
    user = getUser(user_id)
    await context.bot.send_chat_action(
        chat_id=update._effective_chat.id,
        action=ChatAction.UPLOAD_PHOTO,
    )
    try:
        await update.message.reply_photo(photo= profile_pic, 
                               caption=ME_MSG.format(user["first_name"], 
                                                     user["user_name"], 
                                                     user["user_id"],
                                                     AKI_LANG_CODE[user["aki_lang"]],
                                                     "Enabled" if getChildMode(user_id) else "Disabled",
                                                     getTotalGuess(user_id),
                                                     getCorrectGuess(user_id),
                                                     getWrongGuess(user_id),
                                                     getUnfinishedGuess(user_id),
                                                     getTotalQuestions(user_id),
                                                     ),
                               parse_mode=ParseMode.HTML)
    except error.BadRequest as e:
            await  update.message.reply_text( text= PERMISSION_ISSUE,
                                            parse_mode=ParseMode.MARKDOWN,
                                            reply_markup=GUIDE_KEYBOARD
            )
            logging.error(f"Error : {e}")
    
    
    
async def aki_lang(update: Update, context: CallbackContext) -> None:
    """
    This function is used to handle the user's language preference for the Akinator game.
    It takes in an Update object and a CallbackContext object as parameters.
    It retrieves the user's preferred language and sends a message with language options.
    """
    if update.effective_user.username == "GroupAnonymousBot":
        await update.message.reply_text(
            text="Sorry *Anoynomous* players are not allowed to play Akinator.🤫",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=GUIDE_KEYBOARD
        )
        return
    user_id = update.effective_user.id
    addUser(user_id, update.effective_user.first_name, update.effective_user.last_name, update.effective_user.username)
    await update.message.reply_text(AKI_LANG_MSG.format(AKI_LANG_CODE[getLanguage(user_id)]),
                                parse_mode=ParseMode.HTML,
                                reply_markup=AKI_LANG_BUTTON)

async def aki_childmode(update: Update, context: CallbackContext) -> None:
    '''This function is used to handle the user's child mode preference for the Akinator game.'''
    if update.effective_user.username == "GroupAnonymousBot":
        await update.message.reply_text(
            text="Sorry *Anoynomous* players are not allowed to play Akinator.🤫",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=GUIDE_KEYBOARD
        )
        return
    user_id =  update.effective_user.id
    addUser(user_id, update.effective_user.first_name, update.effective_user.last_name, update.effective_user.username)
    status = "enabled" if getChildMode(user_id) else "disabled"
    await update.message.reply_text(
        text=CHILDMODE_MSG.format(status),
        parse_mode=ParseMode.HTML,
        reply_markup=CHILDMODE_BUTTON
    )

async def aki_set_child_mode(update: Update, context: CallbackContext) -> None:
    '''This function is used to set the user's child mode preference for the Akinator game.'''
    user_id = update.effective_user.id
    query = update.callback_query
    to_set = int(query.data.split('_')[-1])
    updateChildMode(user_id, to_set)
    await query.edit_message_text(f"Child mode is {'enabled' if to_set else 'disabled'} Successfully!")
    

async def aki_set_lang(update: Update, context: CallbackContext) -> None:
    '''This function is used to set the user's language preference for the Akinator game.'''
    query = update.callback_query
    lang_code = query.data.split('_')[-1]
    user_id = update.effective_user.id
    updateLanguage(user_id, lang_code)
    query.edit_message_text(f"Language Successfully changed to {AKI_LANG_CODE[lang_code]} !")
    
async def aki_play_cmd_handler(update: Update, context: CallbackContext) -> None:
    '''This function is used to handle the /play command.'''

    #/play command.
    if update.effective_user.username == "GroupAnonymousBot":
        await update.message.reply_text(
            text="Sorry *Anoynomous* players are not allowed to play Akinator.🤫",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=GUIDE_KEYBOARD
        )
        return
    first_name = update.effective_user.first_name
    user_id = update.effective_user.id
    addUser(user_id, update.effective_user.first_name, update.effective_user.last_name, update.effective_user.username)
    aki = Akinator()
    try:
        await context.bot.send_chat_action(
            chat_id=update._effective_chat.id,
            action=ChatAction.UPLOAD_PHOTO,
        )
    except error.BadRequest as e:
        logging.error(f"Error : {e}")
    
    caption = "Loading..." if update.effective_chat.type == "private" else GROUP_LOADING_CAPTION_MSG.format(first_name, user_id)
    parse_mode = ParseMode.MARKDOWN if not update.effective_chat.type == "private" else None

    try:
        msg = await update.message.reply_photo(
        photo=AKI_FIRST_IMG,
        caption=caption,
        parse_mode=parse_mode
        )
    except error.BadRequest as e:
        msg = await update.message.reply_text(
        text=PERMISSION_ISSUE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=GUIDE_KEYBOARD
    )
        logging.error(f"Error: {e}")

    if get_last_msg_id(user_id) is not None:
        try:
            last_message_id =get_last_msg_id(user_id)
            await context.bot.delete_message(chat_id=get_chat_id(user_id, last_message_id), message_id=last_message_id)
        except error.ChatMigrated as e:
            pass
        except error.BadRequest as e:
            logging.error(f"Error : {e}")
        update_last_msg_id(user_id, msg.id, update.effective_chat.id,msg.id)
        
    else :
        add_last_msg_id(user_id, msg.id, update.effective_chat.id,msg.id)
        

    updateTotalGuess(user_id, total_guess=1)
    q = aki.start_game(language=getLanguage(user_id), child_mode=getChildMode(user_id))
    context.user_data[f"aki_{user_id}"] = aki
    
    #context.user_data[f"aki_{user_id}"]  to store the Akinator instance (aki) so that it can be accessed later in the conversation. 
    
    context.user_data[f"q_{user_id}"] = q
    
    #context.user_data[f"q_{user_id}"] stores the current question (q) being asked in the game.
    context.user_data[f"ques_{user_id}"] = 1
    
    #context.user_data[f"ques_{user_id}"]  to keep track of the question number, starting from 1.
    try:
        caption = q if update.effective_chat.type == "private" else MENTION_USER.format(first_name, user_id, q)
        await msg.edit_caption(
        caption=caption,
        reply_markup=AKI_PLAY_KEYBOARD,
        parse_mode=ParseMode.MARKDOWN
     )
    except error.BadRequest as e:
        logging.error(f"Error: {e}")

async def aki_lead(update: Update, _:CallbackContext) -> None:
    if update.effective_user.username == "GroupAnonymousBot":
        await update.message.reply_text(
            text="Sorry *Anoynomous* players are not allowed to play Akinator.🤫",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=GUIDE_KEYBOARD
        )
        return
    await update.message.reply_text(
            text="Check Leaderboard on specific categories in Akinator.",
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )

async def get_lead_total(lead_list: list, lead_category: str) -> str:

    lead = f'Top 10 {lead_category} are :\n'
    for i in lead_list:
        lead = lead+f"{i[0]} : {i[1]}\n"
    return lead


async def del_data(context:CallbackContext, user_id: int):
    del context.user_data[f"q_{user_id}"]
    del context.user_data[f"aki_{user_id}"]


async def aki_play_callback_handler(update: Update, context:CallbackContext) -> None:
        #Handles the inline buttons of /play command 
        user_id = update.effective_user.id
        chat_id= update.effective_chat.id
        query = update.callback_query 
        type = update.effective_chat.type
        msg_id = query.message.id 
        if get_user_id(msg_id,chat_id)==query.from_user.id:
            try :
                aki = context.user_data[f"aki_{user_id}"]
                q = context.user_data[f"q_{user_id}"]
                updateTotalQuestions(user_id, 1)
                a = query.data.split('_')[-1]
                if a == '5':
                    updateTotalQuestions(user_id, -1)
                    try:
                        q = aki.back()
                    except akinator.exceptions.CantGoBackAnyFurther:
                        await query.answer(text=AKI_FIRST_QUESTION, show_alert=True)
                        return
                else:
                    try :
                        q = aki.answer(a) #this returns the next question 
                    except akinator.exceptions.AkiTimedOut:
                        await query.answer(text="you took too long to answer the question. /play again",show_alert=True)
                        try:
                            await query.delete_message()
                        except error.BadRequest as e:
                            logging.error(f"Error : {e}")

                query.answer()
                if aki.progression < 85:
                    v= aki.progression+15
                    v= round(v,2)
                    try:
                        caption = q if type == "private" else MENTION_USER.format(update.effective_user.first_name, user_id, q)
    
                        await query.message.edit_media(
                         InputMediaPhoto(
                            media=generate_random_img(),
                            caption=caption+"\n"+SURETY.format(v),
                            parse_mode=ParseMode.MARKDOWN
                                ),
                            reply_markup=AKI_PLAY_KEYBOARD
                             )
                    except error.BadRequest as e:
                        logging.error(f"Error: {e}")

                    context.user_data[f"aki_{user_id}"] = aki
                    context.user_data[f"q_{user_id}"] = q
                else:
                    aki.win()
                    aki = aki.first_guess
                    if aki['picture_path'] == 'none.jpg':
                        aki['absolute_picture_path'] = NONE_JPG
                    await query.message.edit_media(
                        InputMediaPhoto(media=aki['absolute_picture_path'],
                        caption=f"It's {aki['name']} ({aki['description']})! Was I correct?"
                        ),
                        reply_markup=AKI_WIN_BUTTON
                    )
                    del_data(context, user_id)
            except akinator.exceptions.AkiServerDown:
                    await query.answer(text="Aki server is down currenlty try again later",show_alert=True)
                    try:
                            await query.delete_message()
                    except error.BadRequest as e:
                            logging.error(f"Error : {e}")
            except akinator.exceptions.AkiTechnicalError:
                    await query.answer(text="Aki server is down currenlty try again later",show_alert=True)
                    await query.delete_message()
            except akinator.exceptions.AkiTimedOut:
                    await query.answer(text="you took too long to answer the question. /play again",show_alert=True)
                    try:
                            await query.delete_message()
                    except error.BadRequest as e:
                            logging.error(f"Error : {e}")
            except json.JSONDecodeError as e:
                    await query.answer(text = "Something went wrong, please start a new game",show_alert=True)
                    try:
                            await query.delete_message()
                    except error.BadRequest as e:
                            logging.error(f"Error : {e}")
            except akinator.exceptions.AkiNoQuestions:
                    await query.answer(text="Akinator run out of question 😵‍💫 , please go back and answer them correctly",show_alert=True)
                    return
            except akinator.exceptions.InvalidAnswerError:
                    await query.answer(text="Invalid answer, please try again or start a new game ",show_alert=True)
            except akinator.exceptions.AkiConnectionFailure:
                    await query.answer(text="you took too long to answer the question. /play again",show_alert=True)
                    try:
                            await query.delete_message()
                    except error.BadRequest as e:
                            logging.error(f"Error : {e}")
        else :
             await query.answer(text= "This is not meant for you 😉",show_alert=True)
            
async def get_log(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id == ADMIN_TELEGRAM_USER_ID:
        try:
            with open('bot.log', 'rb') as log_file:
                await context.bot.send_document(chat_id=user_id, document=log_file, filename='bot.log')
        except Exception as e:
            logging.error(f"Error sending log file: {e}")
            await update.message.reply_text(f"error retrieving log file {e}")
    else:
        update.message.reply_text("You don't have permission to access the log file.")
            


async def aki_lead_cb_handler(update: Update, context:CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data.split('_')[-1]
    
    if data == 'cguess':
        text =await  get_lead_total(getLead("correct_guess"), 'correct guesses')
        await query.edit_message_text(
            text= text,
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )
    elif data == 'tguess':
        text =await  get_lead_total(getLead("total_guess"), 'total guesses')
        await query.edit_message_text(
            text= text,
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )
    elif data == 'wguess':
        text =await  get_lead_total(getLead("wrong_guess"), 'wrong guesses')
        await query.edit_message_text(
            text= text,
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )
    elif data == 'tquestions':
        text = await get_lead_total(getLead("total_questions"), 'total questions')
        await query.edit_message_text(
            text= text,
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )

async def aki_win(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    query = update.callback_query
    ans = query.data.split('_')[-1]

    if ans =='y':
        await query.message.edit_media(
            InputMediaPhoto(
                media=AKI_WIN_IMG,
                caption="gg! lets /play again 😍 "
            ),
            reply_markup=SHARE_BUTTON
        )
        updateCorrectGuess(user_id=user_id, correct_guess=1)
    else:
        await query.message.edit_media(
            InputMediaPhoto(
                media=AKI_DEFEATED_IMG,
                caption="bruh :("
            ),
            reply_markup=None
        )
        updateWrongGuess(user_id=user_id, wrong_guess=1)
            
            
async def total_members(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == ADMIN_TELEGRAM_USER_ID:
        total_members = 0
        message_text = ""
        all_group_chat_id = getAllGroups()

        for chat_id in all_group_chat_id:
            try :
                number = await context.bot.get_chat_member_count(chat_id)
                title = gettitle(chat_id)
                message_text += f"Group Name: {title}\nGroup Members👤: {number}\n"
                total_members+=number
            except error.ChatMigrated as e:
                addgroup(e.new_chat_id, update.effective_chat.title, None)
                logging.error(f"Error : {e}")
                continue
            except error.Forbidden as e:
                logging.error(f"Error : {e}")
                continue
            except error.BadRequest as e :
                logging.error(f"Error : {e}")
                continue
        await context.bot.send_message(chat_id=ADMIN_TELEGRAM_USER_ID, text=f'{message_text}\nTotal members👤 : {total_members}')


async def broadcastChat(update: Update, context: CallbackContext) -> None:
    is_broadcast_message = False 
    if update.effective_chat.type =="private":
        if  update.effective_user.id == ADMIN_TELEGRAM_USER_ID:
            if update.message.text:
                if "#broadcast" in update.message.text:
                    is_broadcast_message = True
            elif update.message.caption:
                if "#broadcast" in update.message.caption:
                    is_broadcast_message =True

            if is_broadcast_message :
                success_count = 0
                fail_count = 0
                exceptions = []
                subscribed_users= getAllUserIds()
                for user_id in subscribed_users:
                        try:
                            reply_markup = update.message.reply_markup
                            await context.bot.copy_message(chat_id=user_id,
                                                               from_chat_id=ADMIN_TELEGRAM_USER_ID,
                                                               message_id=update.message.message_id,
                                                               reply_markup=reply_markup,)
                            success_count += 1
                        except error.BadRequest:
                            exceptions.append(f"{user_id}: user not found")
                            fail_count += 1
                            continue
                        except error.Forbidden:
                            exceptions.append(f"{user_id}: User has blocked the bot.")
                            fail_count += 1
                            continue
                            
                        except error.RetryAfter as e:
                            time.sleep(e.retry_after)  # Wait for the recommended time before retrying
                            continue
                        except error as e:
                            exceptions.append(f"{user_id}: {str(e)}")
                            fail_count += 1
                            continue  # Continue to the next user if fails
                        
                logging.critical(f"Success: {success_count} Failed: {fail_count}. EXCEPTIONS{exceptions}")
            else:
                if update.effective_chat.id == ADMIN_TELEGRAM_USER_ID and update.message.reply_to_message!= None:
                    message_id,user_id=find_user_message_data(update.message.reply_to_message.message_id)
                    reply_markup = update.message.reply_markup
                    await context.bot.copy_message(chat_id=user_id,from_chat_id=ADMIN_TELEGRAM_USER_ID,message_id=update.message.message_id,reply_to_message_id=message_id,reply_markup=reply_markup,allow_sending_without_reply=True) 
                
                else:    
                    pass
        else :
            details = await context.bot.forward_message(chat_id=ADMIN_TELEGRAM_USER_ID,
                                                                from_chat_id=update.message.chat_id, message_id=update.message.message_id)
            add_user_message_data(details.message_id,update.message.message_id,update.effective_chat.id)

def main():
    
    logging.basicConfig(
        filename='bot.log',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  
        level=logging.WARNING
        
    )
    try :
        persistence = PicklePersistence(filepath='akinatorbot')
        application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()
        application.add_handler(CommandHandler("start", aki_start))
        application.add_handler(CommandHandler("find", aki_find))#admin command
        application.add_handler(CommandHandler("me", aki_me))
        application.add_handler(CommandHandler('language', aki_lang))
        application.add_handler(CommandHandler('childmode', aki_childmode))
        application.add_handler(CommandHandler('play', aki_play_cmd_handler))
        application.add_handler(CommandHandler('leaderboard', aki_lead))
        application.add_handler(CommandHandler('log', get_log)) #admin command
        application.add_handler(CommandHandler('me', aki_me))
        application.add_handler(CommandHandler('total', total_members)) #admin command

        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, broadcastChat))

        application.add_handler(CallbackQueryHandler(aki_win, pattern=r"aki_win_"))
        application.add_handler(CallbackQueryHandler(aki_play_callback_handler, pattern=r"aki_play_"))
        application.add_handler(CallbackQueryHandler(aki_set_child_mode, pattern=r"c_mode_"))
        application.add_handler(CallbackQueryHandler(aki_set_lang, pattern=r"aki_set_lang_"))
        application.add_handler(CallbackQueryHandler(aki_lead_cb_handler, pattern=r"aki_lead_"))
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except error.NetworkError as e:
        pass
    
    except Exception as e:
        logging.info(f"Error : {e}")


if __name__ == '__main__':
    main()
    
    