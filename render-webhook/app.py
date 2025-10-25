from flask import Flask, request, jsonify
import os
import requests
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Конфигурация (замените на ваши данные)
BOT_API_URL = "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage"
ADMIN_CHAT_ID = "309524694"  # Ваш chat_id

def notify_admin(message):
    """Уведомить админа о событии"""
    try:
        data = {
            "chat_id": ADMIN_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        # Раскомментируйте когда добавите BOT_TOKEN
        # requests.post(BOT_API_URL, json=data)
        print(f"📢 Уведомление: {message}")
    except Exception as e:
        print(f"❌ Ошибка уведомления: {e}")

@app.route('/webhook/yookassa', methods=['POST'])
def yookassa_webhook():
    try:
        webhook_data = request.json
        logging.info("🔔 Получен вебхук от ЮKassa")
        
        event = webhook_data.get('event')
        payment_id = webhook_data.get('object', {}).get('id')
        status = webhook_data.get('object', {}).get('status')
        amount = webhook_data.get('object', {}).get('amount', {})
        
        logging.info(f"💳 Платеж {payment_id}: {event} -> {status}")
        
        # Уведомляем админа
        notify_admin(f"""💳 <b>Новый вебхук</b>

🆔 <b>Платеж:</b> <code>{payment_id}</code>
📊 <b>Статус:</b> {status}
💰 <b>Сумма:</b> {amount.get('value', 0)} {amount.get('currency', 'RUB')}
🎯 <b>Событие:</b> {event}""")
        
        # Здесь будет логика активации подписки
        if status == 'succeeded':
            # TODO: Добавить логику активации подписки
            notify_admin(f"✅ <b>Платеж успешен!</b>\nПлатеж {payment_id} прошел успешно. Нужно активировать подписку.")
        
        return jsonify({"status": "success", "received": True}), 200
        
    except Exception as e:
        logging.error(f"❌ Ошибка обработки вебхука: {e}")
        notify_admin(f"❌ <b>Ошибка вебхука</b>\n{str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/test-webhook', methods=['GET'])
def test_webhook():
    """Тестовая страница для проверки работы"""
    return """
    <h1>Вебхук для ЮKassa работает! ✅</h1>
    <p>URL: <code>/webhook/yookassa</code></p>
    <p>Метод: <code>POST</code></p>
    <p>Статус: 🟢 Активен</p>
    <hr>
    <p>Для тестирования отправьте POST запрос с JSON данными.</p>
    """

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "yookassa-webhook"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
