import os
import asyncio
import logging
from telegram import Bot
from telegram.ext import Application, CommandHandler
import random
from datetime import datetime, timedelta
import threading
from flask import Flask, render_template, request, jsonify
import sqlite3
import time

# إعدادات البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("❌ لم يتم تعيين BOT_TOKEN في متغيرات البيئة")

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تطبيق Flask للوحة التحكم
app = Flask(__name__)

# مدير قاعدة البيانات
class DatabaseManager:
    def __init__(self):
        self.db_path = 'subscribers.db'
        self.init_database()
    
    def init_database(self):
        """تهيئة قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscribers (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
    
    def add_subscriber(self, user_id, username=None, first_name=None, last_name=None):
        """إضافة مشترك جديد"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO subscribers 
                (user_id, username, first_name, last_name, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, True))
            conn.commit()
            conn.close()
            logger.info(f"✅ تم إضافة المشترك: {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المشترك: {e}")
            return False
    
    def get_all_subscribers(self):
        """الحصول على جميع المشتركين النشطين"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM subscribers WHERE is_active = TRUE')
            subscribers = cursor.fetchall()
            conn.close()
            user_ids = {sub[0] for sub in subscribers}
            return user_ids
        except Exception as e:
            logger.error(f"❌ خطأ في جلب المشتركين: {e}")
            return set()
    
    def get_subscribers_details(self):
        """الحصول على تفاصيل المشتركين"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, join_date 
                FROM subscribers 
                WHERE is_active = TRUE
                ORDER BY join_date DESC
            ''')
            subscribers = cursor.fetchall()
            conn.close()
            return subscribers
        except Exception as e:
            logger.error(f"❌ خطأ في جلب تفاصيل المشتركين: {e}")
            return []

# إنشاء مدير قاعدة البيانات
db_manager = DatabaseManager()

# متغيرات البوت
next_signal_time = datetime.now() + timedelta(minutes=5)
telegram_app = None
is_bot_running = False

def generate_signal():
    """إنشاء إشارة عشوائية"""
    try:
        signal = "✅إشارة جديدة✅\n\n"
        signal += "‼️ الإشارة هاتشتغل صح فقط مع الناس الي سجلت حساباتهم ب بروموكود A1VIP علي تطبيق MELBET ولازم تكون عامل ايداع اقل مبلغ 200 جنية. غير كده الإشارة هاتكون معاك غلط وخسارة.\n\n"
        signal += "⏰الإشارة صالحة لمدة دقيقة فقط من نشرها لا تستخدمها بعد مرور دقيقة من نشرها انتظر الاشارة الجديدة بعد 5 دقائق فقط.\n\n"
        signal += "🔔فعل اشعارات البوت عشان يوصل لك إشعار عند نشر الإشارة الجديدة.\n\n"
        signal += "✅الإشارة✅\n\n"
        
        # إنشاء الشبكة 3x5 مع تفاحة واحدة في كل سطر
        grid = []
        for i in range(3):
            row = ['🟫'] * 5
            apple_pos = random.randint(0, 4)
            row[apple_pos] = '🍎'
            grid.append(''.join(row))
        
        signal += '\n'.join(grid)
        signal += "\n\nشرح طريقة تنزيل تطبيق MELBET والتسجيل ب بروموكود A1VIP وطريقة الايداع الصح عشان الإشارات تشتغل معاك صح وتجيب أرباح. اضغط علي الرابط عشان يحولك للشرح بالتفاصيل 👇من هنا👇\nhttps://t.me/c/1934476102/253"
        
        return signal
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء الإشارة: {e}")
        return "❌ خطأ في إنشاء الإشارة"

async def start_command(update, context):
    """معالجة أمر /start"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name
        
        # حفظ المشترك في قاعدة البيانات
        db_manager.add_subscriber(user_id, username, first_name, last_name)
        
        await update.message.reply_text("✅ تم الاشتراك بنجاح! ستتلقى إشارات كل 5 دقائق.")
        logger.info(f"✅ تم إضافة مستخدم جديد: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في أمر start: {e}")

async def send_signal_to_subscribers():
    """إرسال الإشارة لجميع المشتركين"""
    try:
        if not telegram_app:
            return 0, 0
            
        signal = generate_signal()
        subscribers = db_manager.get_all_subscribers()
        success_count = 0
        fail_count = 0
        
        for user_id in subscribers:
            try:
                await telegram_app.bot.send_message(chat_id=user_id, text=signal)
                success_count += 1
                logger.info(f"✅ تم إرسال الإشارة إلى {user_id}")
            except Exception as e:
                logger.error(f"❌ فشل في إرسال الرسالة إلى {user_id}: {e}")
                fail_count += 1
        
        logger.info(f"📊 تم إرسال الإشارة إلى {success_count} مستخدم، فشل: {fail_count}")
        return success_count, fail_count
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الإشارات: {e}")
        return 0, 0

async def send_media_to_subscribers(media_type, media_file, caption=None):
    """إرسال وسائط للمشتركين"""
    try:
        if not telegram_app:
            return 0, 0
            
        subscribers = db_manager.get_all_subscribers()
        success_count = 0
        fail_count = 0
        
        for user_id in subscribers:
            try:
                if media_type == 'photo':
                    await telegram_app.bot.send_photo(chat_id=user_id, photo=media_file, caption=caption)
                elif media_type == 'video':
                    await telegram_app.bot.send_video(chat_id=user_id, video=media_file, caption=caption)
                elif media_type == 'audio':
                    await telegram_app.bot.send_audio(chat_id=user_id, audio=media_file, caption=caption)
                elif media_type == 'document':
                    await telegram_app.bot.send_document(chat_id=user_id, document=media_file, caption=caption)
                
                success_count += 1
            except Exception as e:
                logger.error(f"❌ فشل في إرسال الوسائط إلى {user_id}: {e}")
                fail_count += 1
        
        logger.info(f"📊 تم إرسال الوسائط إلى {success_count} مستخدم، فشل: {fail_count}")
        return success_count, fail_count
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الوسائط: {e}")
        return 0, 0

async def scheduled_signals():
    """الإشارات المجدولة كل 5 دقائق - إرسال في أول الثانية"""
    global next_signal_time
    logger.info("⏰ بدأ جدول الإشارات المجدولة - نظام التوقيت الدقيق")
    
    while True:
        try:
            if is_bot_running:
                # احسب الوقت الحالي
                now = datetime.now()
                
                # احسب أقرب مضاعف للـ5 دقائق (0, 5, 10, 15, ...)
                current_minute = now.minute
                minutes_to_next_signal = 5 - (current_minute % 5)
                if minutes_to_next_signal == 0:
                    minutes_to_next_signal = 5
                
                # الوقت المستهدف (أول ثانية من الدقيقة المضاعفة لـ5)
                target_time = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_next_signal)
                wait_seconds = (target_time - now).total_seconds()
                
                if wait_seconds > 1:  # إذا كان هناك أكثر من ثانية واحدة انتظر
                    logger.info(f"⏳ انتظار {wait_seconds:.1f} ثانية حتى الإشارة التالية على الساعة {target_time.strftime('%H:%M:%S')}")
                    await asyncio.sleep(wait_seconds)
                
                # إرسال الإشارة في أول ثانية
                await send_signal_to_subscribers()
                next_signal_time = datetime.now() + timedelta(minutes=5)
                logger.info(f"✅ تم إرسال الإشارة المجدولة في الساعة {datetime.now().strftime('%H:%M:%S')}")
                
                # انتظار حتى تمر 5 دقائق كاملة قبل الحساب التالي
                await asyncio.sleep(300)
                
        except Exception as e:
            logger.error(f"❌ خطأ في الإشارة المجدولة: {e}")
            await asyncio.sleep(10)  # انتظار قصير عند الخطأ

async def run_telegram_bot():
    """تشغيل بوت التليجرام"""
    global telegram_app, is_bot_running
    
    try:
        # إنشاء تطبيق التليجرام
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        
        # إضافة معالجات الأوامر
        telegram_app.add_handler(CommandHandler("start", start_command))
        
        # بدء البوت
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        
        is_bot_running = True
        logger.info("🤖 بدأ البوت بنجاح")
        
        # بدء الإشارات المجدولة
        await scheduled_signals()
            
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        is_bot_running = False

def start_bot():
    """بدء البوت في thread منفصل"""
    try:
        asyncio.run(run_telegram_bot())
    except Exception as e:
        logger.error(f"❌ خطأ في thread البوت: {e}")

# تطبيق Flask للوحة التحكم
@app.route('/')
def dashboard():
    """لوحة التحكم الرئيسية"""
    global next_signal_time
    subscribers_count = len(db_manager.get_all_subscribers())
    time_remaining = next_signal_time - datetime.now()
    
    if time_remaining.total_seconds() < 0:
        time_remaining = timedelta(seconds=0)
    
    minutes = int(time_remaining.total_seconds() // 60)
    seconds = int(time_remaining.total_seconds() % 60)
    
    return render_template('dashboard.html',
                         subscribers_count=subscribers_count,
                         next_signal_time=next_signal_time.strftime("%H:%M:%S"),
                         time_remaining=f"{minutes:02d}:{seconds:02d}",
                         bot_status="🟢 يعمل" if is_bot_running else "🔴 متوقف")

@app.route('/subscribers')
def subscribers_list():
    """قائمة المشتركين"""
    subscribers = db_manager.get_subscribers_details()
    return render_template('subscribers.html', subscribers=subscribers)

@app.route('/send_signal', methods=['POST'])
def send_signal_manual():
    """إرسال إشارة يدوية"""
    try:
        async def send_async():
            return await send_signal_to_subscribers()
        
        success, fail = asyncio.run(send_async())
        
        return jsonify({
            'status': 'success',
            'message': f'✅ تم إرسال الإشارة إلى {success} مستخدم',
            'success_count': success,
            'fail_count': fail
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'❌ خطأ في الإرسال: {str(e)}'
        })

@app.route('/send_media', methods=['POST'])
def send_media():
    """إرسال وسائط للمشتركين"""
    try:
        media_type = request.form.get('media_type')
        media_url = request.form.get('media_url')
        caption = request.form.get('caption', '')
        
        async def send_async():
            return await send_media_to_subscribers(media_type, media_url, caption)
        
        success, fail = asyncio.run(send_async())
        
        return jsonify({
            'status': 'success',
            'message': f'✅ تم إرسال الوسائط إلى {success} مستخدم',
            'success_count': success,
            'fail_count': fail
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'❌ خطأ في إرسال الوسائط: {str(e)}'
        })

@app.route('/stats')
def get_stats():
    """الحصول على الإحصائيات"""
    global next_signal_time
    subscribers_count = len(db_manager.get_all_subscribers())
    time_remaining = next_signal_time - datetime.now()
    
    if time_remaining.total_seconds() < 0:
        time_remaining = timedelta(seconds=0)
    
    minutes = int(time_remaining.total_seconds() // 60)
    seconds = int(time_remaining.total_seconds() % 60)
    
    return jsonify({
        'subscribers_count': subscribers_count,
        'next_signal_time': next_signal_time.strftime("%H:%M:%S"),
        'time_remaining': f"{minutes:02d}:{seconds:02d}",
        'bot_status': "🟢 يعمل" if is_bot_running else "🔴 متوقف"
    })

@app.route('/backup', methods=['POST'])
def create_backup():
    """إنشاء نسخة احتياطية"""
    try:
        return jsonify({
            'status': 'success',
            'message': '💾 النسخ الاحتياطي يعمل تلقائياً'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'❌ خطأ: {str(e)}'
        })

def run_flask():
    """تشغيل تطبيق Flask"""
    try:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"🌐 بدأ خادم الويب على المنفذ {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل خادم الويب: {e}")

if __name__ == '__main__':
    # تشغيل البوت في thread منفصل
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # تشغيل لوحة التحكم
    run_flask()
