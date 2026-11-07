import os
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))


async def is_admin(update, context):
    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat or chat.type == "private":
        return False

    if user.id == OWNER_ID:
        return True

    member = await chat.get_member(user.id)
    return member.status in ("administrator", "creator")


async def get_target(update, context):
    msg = update.effective_message

    if msg.reply_to_message:
        return msg.reply_to_message.from_user.id

    if context.args:
        try:
            return int(context.args[0])
        except ValueError:
            return None

    return None


async def moderate(update, context, action):
    if not await is_admin(update, context):
        await update.effective_message.reply_text("🚫 Нет прав!")
        return

    target = await get_target(update, context)

    if not target:
        await update.effective_message.reply_text(
            "Ответь на сообщение пользователя или укажи Telegram ID."
        )
        return

    chat_id = update.effective_chat.id
    bot = context.bot

    try:
        if action == "ban":
            await bot.ban_chat_member(chat_id, target)
            result = "🚫 Пользователь забанен!"

        elif action == "unban":
            await bot.unban_chat_member(chat_id, target)
            result = "✅ Бан снят!"

        elif action == "mute":
            await bot.restrict_chat_member(
                chat_id, target,
                ChatPermissions(can_send_messages=False)
            )
            result = "🔇 Пользователь получил мут!"

        else:
            await bot.restrict_chat_member(
                chat_id, target,
                ChatPermissions(
                    can_send_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            result = "🔊 Мут снят!"

        await update.effective_message.reply_text(result)

    except Exception as e:
        await update.effective_message.reply_text(f"Ошибка: {e}")


async def ban(u, c):
    await moderate(u, c, "ban")


async def unban(u, c):
    await moderate(u, c, "unban")


async def mute(u, c):
    await moderate(u, c, "mute")


async def unmute(u, c):
    await moderate(u, c, "unmute")


def main():
    if not TOKEN or OWNER_ID == 0:
        raise RuntimeError("Настрой BOT_TOKEN и OWNER_ID")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))

    print("Admin Bot запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
