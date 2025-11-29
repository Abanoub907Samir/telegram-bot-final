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

if name == 'main':
    # تشغيل البوت في thread منفصل
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # تشغيل لوحة التحكم
    run_flask()
