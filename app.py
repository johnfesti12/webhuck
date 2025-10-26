from flask import Flask, request, jsonify
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Хранилище для вебхуков (временное)
webhooks_received = []

@app.route('/webhook/yookassa', methods=['POST'])
def yookassa_webhook():
    try:
        data = request.json
        logging.info(f"🔔 Получен вебхук: {data}")
        
        # Сохраняем вебхук
        webhooks_received.append({
            'payment_id': data.get('object', {}).get('id'),
            'event': data.get('event'),
            'status': data.get('object', {}).get('status'),
            'timestamp': os.times().user
        })
        
        # Здесь можно добавить логику для уведомления вашего бота
        # Например, отправить запрос на ваш сервер с ботом
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhooks', methods=['GET'])
def list_webhooks():
    """Посмотреть все полученные вебхуки"""
    return jsonify({
        "count": len(webhooks_received),
        "webhooks": webhooks_received[-10:]  # Последние 10
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "yookassa-webhook"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)