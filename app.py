from flask import Flask, render_template, request, redirect, url_for, session
import socket
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = "gizli_anahtar"  # Oturum için gizli anahtar

# Veritabanı benzeri bir yapı (geçici olarak list kullanıyoruz)
records = []

# Şifre (admin paneli için)
ADMIN_PASSWORD = "admin123"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    action = request.form.get('action')  # 'Giriş' veya 'Çıkış'
    name = request.form.get('name')  # Çalışanın adı
    if action and name:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Zaman damgası
        record = {'name': name, 'action': action, 'timestamp': timestamp}
        records.append(record)  # Veriyi kaydet

        # Mesajı sunucuya gönder
        message = f"{name} - {action} - {timestamp}"
        send_message_to_server(message)
        return f"{name} için {action} işlemi yapıldı."
    return "Geçersiz giriş!"

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True  # Oturum açılıyor
            return redirect(url_for('admin_dashboard'))
        else:
            return "Hatalı şifre!", 403  # Hata durumu
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):  # Oturum açık değilse
        return redirect(url_for('admin_panel'))
    return render_template('admin.html', records=records)

@app.route('/logout')
def logout():
    session.pop('admin', None)  # Oturumu kapat
    return redirect(url_for('index'))

# Soket sunucusu
def socket_server():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Port yeniden kullanımı
        server_socket.bind(("127.0.0.1", 8081))  # IP ve Port
        server_socket.listen(1)  # Gelen bağlantıları dinle

        print("Sunucu başlatıldı. Port: 8081 dinleniyor...")

        while True:
            client_socket, address = server_socket.accept()
            print(f"Yeni bağlantı kabul edildi: {address}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        server_socket.close()

# İstemciden gelen mesajları işleme
def handle_client(client_socket):
    with client_socket:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            print(f"Mesaj alındı: {data}")

# Flask ile sunucuya mesaj gönderme
def send_message_to_server(message):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("127.0.0.1", 8081))
        client_socket.sendall(message.encode())
        client_socket.close()
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

# Sunucu iş parçacığını başlat
server_thread = threading.Thread(target=socket_server, daemon=True)
server_thread.start()

# Flask uygulamasını başlat
if __name__ == '__main__':
    app.run(debug=True, port=5000)