# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# utils.py

import os
from datetime import datetime
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import threading

load_dotenv()

encryptionKey = os.getenv("ENCRYPTION_KEY")
cipherSuite = Fernet(encryptionKey.encode()) if encryptionKey else None

def getNow(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def log(level, message): print(f"[{getNow()}] [{level}] {message}", flush=True)

def encryptData(data):
    if not data: return None
    return cipherSuite.encrypt(data.encode()).decode()

def decryptData(encryptedData):
    if not encryptedData: return None
    return cipherSuite.decrypt(encryptedData.encode()).decode()

# step timeout
userTimers = {}

def startStepTimeout(bot, chatId, seconds=60):
    cancelStepTimeout(chatId)
    
    def timeoutCallback():
        try:
            bot.clear_step_handler_by_chat_id(chatId)
            bot.send_message(chatId, "⏰ <b>Hết thời gian!</b>\nLệnh của bạn đã bị hủy do quá lâu không có phản hồi.", parse_mode="HTML")
            log("TIMEOUT", f"Đã hủy lệnh chờ của user {chatId} do hết thời gian.")
        except Exception as e:
            log("ERROR", f"Lỗi khi xử lý timeout: {e}")
        finally:
            if chatId in userTimers:
                del userTimers[chatId]

    timer = threading.Timer(seconds, timeoutCallback)
    timer.start()
    userTimers[chatId] = timer

def cancelStepTimeout(chatId):
    if chatId in userTimers:
        userTimers[chatId].cancel()
        del userTimers[chatId]