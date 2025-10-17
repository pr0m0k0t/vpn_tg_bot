import re
import time

def escape_markdown_v2(text):
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


def start_message(username):
    message = (f"👋 Привет, {username}\\!\n\n "
               f"Твоя *пробная подписка* уже активирована ✅\n"
               f"🎉 _3 дня бесплатного доступа_ к нашему VPN 🚀\n"
               f"Подключай устройство и наслаждайся свободой интернета 🌍")
    return message


def success_message(username, expiry_time):
    strf = escape_markdown_v2(time.strftime('%d.%m.%Y', time.localtime(expiry_time)))
    message = (f"👋 Привет, {username}\\!\n\n "
               f"Твоя *подписка* активна до {strf}✅\n"
               f"Подключай устройство и наслаждайся свободой интернета 🌍")
    return message


def choose_device():
    message = (f" Выбери *устройство*, которое хочешь подключить\\:\n\n"
               f"📱 IPhone\n"
               f"☎️ Смартфон Android\n"
               f"🖥️ Компьютер Windows\n"
               f"💻 Компьютер MacOS\n")
    return message


def help_message():
    supp_link = escape_markdown_v2("@vpn_supp0rtbot")
    message = (f"⚠️ Возникли *проблемы*\\?\n"  
                f"📩 Напиши в поддержку, и мы поможем решить всё максимально быстро 🛠\n\n️"
                f"{supp_link}\n\n"
                f"_Мы всегда на связи\\!_")
    return message


def ref_link(ref_link):
    ref = escape_markdown_v2(ref_link)
    message = (f"🤝 Делись свободой интернета с друзьями\\!\n\n"  
                f"🔗 Ваша *пригласительная ссылка*\\: {ref}\n\n"  
                f"🎁 За каждого друга мы дарим тебе _3 дополнительных дня_ подписки 🚀\n"  
                f"*Больше друзей → больше интернета без границ\\!*")
    return message

def success_pay(new_expiry):
    strf = escape_markdown_v2(time.strftime('%d.%m.%Y', time.localtime(new_expiry)))
    message = (f"Спасибо за оплату\\! Подписка продлена до {strf}✅\n\n"
            f"Для установки VPN на своё устройство следуйте инструкциям")

    return message
