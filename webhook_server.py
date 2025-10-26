from flask import Flask, request, jsonify
from datetime import datetime
import logging
import os
import sqlite3
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class SimpleSubscriptionManager:
    def __init__(self):
        self.db_path = 'psychology_bot.db'
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.create_tables()
            logger.info("✅ База данных подписок инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                subscription_type TEXT NOT NULL DEFAULT 'free',
                expiry_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def add_premium_user(self, user_id, days=30):
        """Добавить премиум подписку пользователю"""
        try:
            cursor = self.conn.cursor()
            expiry_date = datetime.now() + timedelta(days=days)
            
            cursor.execute('''
                INSERT OR REPLACE INTO subscriptions 
                (user_id, subscription_type, expiry_date) 
                VALUES (?, ?, ?)
            ''', (user_id, 'premium', expiry_date))
            
            self.conn.commit()
            logger.info(f"✅ Пользователю {user_id} добавлен премиум на {days} дней")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления премиума: {e}")
            return False

# Инициализируем менеджер подписок
sub_manager = SimpleSubscriptionManager()

@app.route('/webhook/yookassa', methods=['POST', 'GET'])
def yookassa_webhook():
    try:
        if request.method == 'GET':
            logger.info("✅ ЮKassa проверяет вебхук")
            return jsonify({
                "status": "ready", 
                "service": "yookassa-webhook",
                "timestamp": datetime.now().isoformat()
            }), 200
            
        # Обработка POST запросов (реальные вебхуки)
        webhook_data = request.json
        event_type = webhook_data.get('event', 'unknown')
        payment_id = webhook_data.get('object', {}).get('id', 'unknown')
        payment_status = webhook_data.get('object', {}).get('status', 'unknown')
        
        logger.info(f"🔔 Получен вебхук: {event_type}, статус: {payment_status}, ID: {payment_id}")
        
        # Обрабатываем успешный платеж
        if event_type == 'payment.succeeded' and payment_status == 'succeeded':
            # Ищем user_id в метаданных платежа
            metadata = webhook_data.get('object', {}).get('metadata', {})
            user_id = metadata.get('user_id')
            
            if user_id:
                try:
                    user_id = int(user_id)
                    success = sub_manager.add_premium_user(user_id, 30)
                    if success:
                        logger.info(f"🎉 Подписка активирована для пользователя {user_id}")
                        return jsonify({
                            "success": True, 
                            "message": "Subscription activated",
                            "user_id": user_id,
                            "days_added": 30
                        }), 200
                except (ValueError, TypeError) as e:
                    logger.error(f"❌ Неверный user_id: {user_id}")
            
            # Если user_id не найден, просто логируем
            logger.info(f"💰 Платеж успешен, но user_id не найден. ID платежа: {payment_id}")
            return jsonify({
                "success": True, 
                "message": "Payment received, but user_id not found in metadata",
                "payment_id": payment_id
            }), 200
        
        return jsonify({
            "success": True, 
            "message": "Webhook received",
            "event": event_type,
            "payment_id": payment_id
        }), 200
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки вебхука: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "yookassa-webhook",
        "version": "2.0",
        "webhook_url": "https://yookassa-webhook-5soq.onrender.com/webhook/yookassa"
    })

@app.route('/test_activate/<int:user_id>', methods=['GET'])
def test_activate(user_id):
    """Тестовый endpoint для активации подписки"""
    try:
        success = sub_manager.add_premium_user(user_id, 30)
        if success:
            return jsonify({
                "success": True,
                "message": f"Test subscription activated for user {user_id}",
                "user_id": user_id,
                "days": 30
            }), 200
        else:
            return jsonify({"error": "Failed to activate subscription"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        "message": "Yookassa Webhook Server", 
        "status": "active",
        "endpoints": [
            {"path": "/webhook/yookassa", "methods": ["GET", "POST"], "description": "Основной вебхук для ЮKassa"},
            {"path": "/health", "methods": ["GET"], "description": "Проверка здоровья сервера"},
            {"path": "/test_activate/<user_id>", "methods": ["GET"], "description": "Тест активации подписки"},
            {"path": "/", "methods": ["GET"], "description": "Информация о сервере"}
        ]
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"🚀 Запуск вебхук-сервера на порту {port}")
    logger.info(f"🔗 Основной URL: https://yookassa-webhook-5soq.onrender.com")
    logger.info(f"🎯 Вебхук endpoint: /webhook/yookassa")
    app.run(host='0.0.0.0', port=port, debug=False)
