from flask import Flask, jsonify

app = Flask(__name__)

# SSRFの攻撃対象となる内部API
@app.route('/internal')
def internal_api():
    secret_data = {
        "service_name": "Project C-56 (Database)",
        "credentials": {
            "db_host": "db.nerv.tokyo-3.local",
            "db_port": 5432,
            "db_user": "admin",
            "db_password": "No_one_can_stop_us_now_42!"
        },
        "status": "ACTIVE",
        "confidentiality_level": "ULTRA"
    }
    return jsonify(secret_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)