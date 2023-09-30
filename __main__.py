import time 
from random import randint
from akinator import Akinator
from telegram import Update ,InputMediaPhoto
from keyboard import AKI_LANG_BUTTON, AKI_LEADERBOARD_KEYBOARD, AKI_PLAY_KEYBOARD, AKI_WIN_BUTTON, CHILDMODE_BUTTON, START_KEYBOARD,SHARE_BUTTON
from telegram.constants import ParseMode,ChatAction
from telegram.ext import Application,CommandHandler
from telegram.ext import  CommandHandler, CallbackContext, CallbackQueryHandler,filters, MessageHandler
from config import BOT_TOKEN,ADMIN_TELEGRAM_USER_ID
import logging 
from database import (
    addUser, 
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
    getAllUserIds)

from strings import AKI_FIRST_QUESTION, AKI_LANG_CODE, AKI_LANG_MSG, CHILDMODE_MSG, ME_MSG, START_MSG
import akinator

global is_pin_message
is_pin_message=False
async def aki_start(update: Update, context: CallbackContext) -> None:
    #/start command.
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    user_name = update.effective_user.username
    #Adding user to the database.
    addUser(user_id, first_name, last_name, user_name)
    await context.bot.send_chat_action(
        chat_id=update.effective_user.id,
        action=ChatAction.TYPING,
    )

    await update.message.reply_text(START_MSG.format(first_name), 
                              parse_mode=ParseMode.HTML, 
                              reply_markup=START_KEYBOARD)

async def aki_find(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == 6023650727:
        total_users = totalUsers()
        await update.message.reply_text(f"Users : {total_users}")
    else:
        pass


async def pin_message(update: Update, context: CallbackContext) -> None:
    global is_pin_message
    if is_pin_message== True:
        is_pin_message= False
        await update.message.reply_text("Next message will not be pinned.")
    else :
        is_pin_message= True
        await update.message.reply_text("Next message will  be pinned.")


async def aki_me(update: Update, context: CallbackContext) -> None:
    #/me command
    user_id = update.effective_user.id
    profile_pic =( await  update.effective_user.get_profile_photos(limit=1)).photos
    if len(profile_pic) == 0:
        profile_pic = "https://telegra.ph/file/a65ee7219e14f0d0225a9.png"
    else:
        profile_pic = profile_pic[0][1]
    user = getUser(user_id)
    await context.bot.send_chat_action(
        chat_id=update.effective_user.id,
        action=ChatAction.UPLOAD_PHOTO,
    )
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

async def aki_lang(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(AKI_LANG_MSG.format(AKI_LANG_CODE[getLanguage(user_id)]),
                                parse_mode=ParseMode.HTML,
                                reply_markup=AKI_LANG_BUTTON)

async def aki_childmode(update: Update, context: CallbackContext) -> None:
    user_id =  update.effective_user.id
    status = "enabled" if getChildMode(user_id) else "disabled"
    await update.message.reply_text(
        text=CHILDMODE_MSG.format(status),
        parse_mode=ParseMode.HTML,
        reply_markup=CHILDMODE_BUTTON
    )

async def aki_set_child_mode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    query = update.callback_query
    to_set = int(query.data.split('_')[-1])
    updateChildMode(user_id, to_set)
    await query.edit_message_text(f"Child mode is {'enabled' if to_set else 'disabled'} Successfully!")
    

async def aki_set_lang(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    lang_code = query.data.split('_')[-1]
    user_id = update.effective_user.id
    updateLanguage(user_id, lang_code)
    query.edit_message_text(f"Language Successfully changed to {AKI_LANG_CODE[lang_code]} !")
async def aki_play_cmd_handler(update: Update, context: CallbackContext) -> None:

    #/play command.

    user_id = update.effective_user.id
    aki = Akinator()
    await context.bot.send_chat_action(
        chat_id=update.effective_user.id,
        action=ChatAction.UPLOAD_PHOTO,
    )
    msg = await update.message.reply_photo(
        photo=open('aki_pics/aki_01.png', 'rb'),
        caption="Loading..."
    )
    
    
    updateTotalGuess(user_id, total_guess=1)
    q = aki.start_game(language=getLanguage(user_id), child_mode=getChildMode(user_id))

    context.user_data[f"aki_{user_id}"] = aki #context.user_data[f"aki_{user_id}"] appears to store the Akinator instance (aki) so that it can be accessed later in the conversation. 
    context.user_data[f"q_{user_id}"] = q
    #context.user_data[f"q_{user_id}"] stores the current question (q) being asked in the game.
    context.user_data[f"ques_{user_id}"] = 1
    #context.user_data[f"ques_{user_id}"] seems to keep track of the question number, starting from 1.

    await msg.edit_caption(
        caption=q,
        reply_markup=AKI_PLAY_KEYBOARD
        )

async def aki_lead(update: Update, _:CallbackContext) -> None:
    if update.effective_user.id == ADMIN_TELEGRAM_USER_ID:
        await update.message.reply_text(
            text="Check Leaderboard on specific categories in Akinator.",
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )
    else:
        pass

async def get_lead_total(lead_list: list, lead_category: str) -> str:
    lead = f'Top 10 {lead_category} are :\n'
    for i in lead_list:
        lead = lead+f"{i[0]} : {i[1]}\n"
    return lead


async def del_data(context:CallbackContext, user_id: int):
    del context.user_data[f"q_{user_id}"]
    del context.user_data[f"aki_{user_id}"]


async def aki_play_callback_handler(update: Update, context:CallbackContext) -> None:
    user_id = update.effective_user.id
    aki = context.user_data[f"aki_{user_id}"]
    q = context.user_data[f"q_{user_id}"]
    updateTotalQuestions(user_id, 1)
    query = update.callback_query
    a = query.data.split('_')[-1]
    if a == '5':
        updateTotalQuestions(user_id, -1)
        try:
            q = aki.back()
        except akinator.exceptions.CantGoBackAnyFurther:
            await query.answer(text=AKI_FIRST_QUESTION, show_alert=True)
            return
    else:
        q = aki.answer(a) #this returns the next question 
        
    query.answer()
    if aki.progression < 80:
        await query.message.edit_media(
            InputMediaPhoto(
                open(f'aki_pics/aki_0{randint(1,5)}.png', 'rb'),
                caption=q,
            ),
            reply_markup=AKI_PLAY_KEYBOARD
        )
        context.user_data[f"aki_{user_id}"] = aki
        context.user_data[f"q_{user_id}"] = q
    else:
        aki.win()
        aki = aki.first_guess
        if aki['picture_path'] == 'none.jpg':
            aki['absolute_picture_path'] = open('aki_pics/none.jpg', 'rb')
        await query.message.edit_media(
            InputMediaPhoto(media=aki['absolute_picture_path'],
            caption=f"It's {aki['name']} ({aki['description']})! Was I correct?"
            ),
            reply_markup=AKI_WIN_BUTTON
        )
        del_data(context, user_id)

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
    # print(query.data)
    data = query.data.split('_')[-1]
    # print(data)
    await context.bot.send_chat_action(
        chat_id=update.effective_user.id,
        action=ChatAction.TYPING,
    )
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
                media=open('aki_pics/aki_win.png', 'rb'),
                caption="gg!"
            ),
            reply_markup=SHARE_BUTTON
        )
        updateCorrectGuess(user_id=user_id, correct_guess=1)
    else:
        await query.message.edit_media(
            InputMediaPhoto(
                media=open('aki_pics/aki_defeat.png', 'rb'),
                caption="bruh :("
            ),
            reply_markup=None
        )
        updateWrongGuess(user_id=user_id, wrong_guess=1)


async def forward_messege(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == ADMIN_TELEGRAM_USER_ID:
            subscribed_users= getAllUserIds()
            try:
                i = 0
                for user_id in subscribed_users:
                    i+=1
                    if i%30 == 0:
                        time.sleep(1)
                    else :
                        if update.message.reply_markup and update.message.reply_markup.inline_keyboard:
                            forwarded_message=  await  context.bot.forward_message(chat_id=user_id, 
                                                    from_chat_id=update.message.chat_id, message_id=update.message.message_id,
                                                    disable_notification=False)
                            if is_pin_message:
                                await context.bot.pin_chat_message(chat_id=user_id, message_id=forwarded_message.message_id)
                        else :
                            copied_message = await context.bot.copy_message(chat_id=user_id,
                                                 from_chat_id=update.message.chat_id, message_id=update.message.message_id)
                            if is_pin_message:
                                     await context.bot.pin_chat_message(chat_id=user_id, message_id=copied_message.message_id)
                    logging.info(f"Message forwarded to {len(subscribed_users)} users")
            except Exception as e:
                logging.error(f"Error forwarding : {e}")
    else :
        await update.message.reply_text("send /play for playing Akinator")
            
            




def main():
    
    logging.basicConfig(
        filename='bot.log',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  
        level=logging.WARNING
        
    )
    try :
        
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", aki_start))
        application.add_handler(CommandHandler("find", aki_find))
        application.add_handler(CommandHandler("me", aki_me))
        application.add_handler(CommandHandler('language', aki_lang))
        application.add_handler(CommandHandler('childmode', aki_childmode))
        application.add_handler(CommandHandler('play', aki_play_cmd_handler))
        application.add_handler(CommandHandler('leaderboard', aki_lead))
        application.add_handler(CommandHandler('log', get_log))
        application.add_handler(CommandHandler('me', aki_me))
        application.add_handler(CommandHandler('pin', pin_message))
        
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_messege))
        
        application.add_handler(CallbackQueryHandler(aki_win, pattern=r"aki_win_"))
        application.add_handler(CallbackQueryHandler(aki_play_callback_handler, pattern=r"aki_play_"))
        application.add_handler(CallbackQueryHandler(aki_set_child_mode, pattern=r"c_mode_"))
        application.add_handler(CallbackQueryHandler(aki_set_lang, pattern=r"aki_set_lang_"))
        application.add_handler(CallbackQueryHandler(aki_lead_cb_handler, pattern=r"aki_lead_"))
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logging.info(f"Error : {e}")

if __name__ == '__main__':
    main()
