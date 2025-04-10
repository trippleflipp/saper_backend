from app import create_app, db
import ssl

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # cert_file = "ssl_cert.pem"
    # key_file = "ssl_key.pem"
    port = 80

    # context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # context.load_cert_chain(cert_file, key_file)

    app.run(host="0.0.0.0", port=port)