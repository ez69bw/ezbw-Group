from typing import Optional

from telegram import Message, Update, Bot, User
from telegram import MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, run_async

from haruka import dispatcher
from haruka.modules.disable import DisableAbleCommandHandler, DisableAbleRegexHandler
from haruka.modules.sql import afk_sql as sql
from haruka.modules.users import get_user_id

from haruka.modules.translations.strings import tld

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


@run_async
def afk(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)
    if len(args) >= 2:
        reason = args[1]
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    update.effective_message.reply_text(tld(chat.id, f"ada awan diatas koboy\n{fname} cabut dulu boy!"))


@run_async
def no_longer_afk(bot: Bot, update: Update):
    user = update.effective_user
    message = update.effective_message

    if not user:  # ignore channels
        return

    res = sql.rm_afk(user.id)
    if res:
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} abis darimana? puas mulung nya?",
                "{} abis sad nih kayanya ditinggal kawin, yakan? ngaku!",
                "hii {}, so sibuk banget segala off!",
                "{} abis overthinking nih bg? yakan yakan!",
                "eyo wassup {}, apakabs kawan?",
                "pasti {} abis hibernasi yakan? jujur aja!",
                "anjas {} anak pungut udah balik lagi xixi",
                "kiw {} kemana aja? ak kangen hm",
            ]
            chosen_option = random.choice(options)
            update.effective_message.reply_text(chosen_option.format(firstname))
        except:
            return


@run_async
def reply_afk(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION, MessageEntity.MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION, MessageEntity.MENTION])
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

            elif ent.type == MessageEntity.MENTION:
                user_id = get_user_id(message.text[ent.offset:ent.offset + ent.length])
                if not user_id:
                    # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                    return
                try:
                    chat = bot.get_chat(user_id)
                except BadRequest:
                    print("Error: Could not fetch userid {} for AFK module".format(user_id))
                    return
                fst_name = chat.first_name

            else:
                return

            check_afk(bot, update, user_id, fst_name)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(bot, update, user_id, fst_name)


def check_afk(bot, update, user_id, fst_name):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_afk(user_id):
        user = sql.check_afk_status(user_id)
        if not user.reason:
            res = tld(chat.id, f"{fst_name} lagi cabut sebentar!")
        else:
            res = tld(chat.id, f"{fst_name} lagi cabut dulu!\nkatanya sih : {user.reason}")
        update.effective_message.reply_text(res)


__help__ = """
 - /afk <reason>: mark yourself as AFK.
 - brb <reason>: same as the afk command - but not a command.

When marked as AFK, any mentions will be replied to with a message to say that you're not available!
"""

__mod_name__ = "AFK"

AFK_HANDLER = DisableAbleCommandHandler("afk", afk)
AFK_REGEX_HANDLER = DisableAbleRegexHandler("(?i)brb", afk, friendly="afk")
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_afk)
AFK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.group, reply_afk)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)
