from app import create_app, db
import ssl

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    cert_file = "ssl_cert.pem"
    key_file = "ssl_key.pem"

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)

    app.run(host="0.0.0.0", port=2365, ssl_context=(cert_file, key_file))