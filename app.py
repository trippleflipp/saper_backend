from app import create_app, db
import ssl
try:
    from waitress import serve
    import waitress  # Import waitress here as well
except ImportError as e:
    print(f"Error importing waitress: {e}")
    print("Please ensure waitress is installed.  Try: pip install waitress")
    exit(1)


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    cert_file = "ssl_cert.pem"
    key_file = "ssl_key.pem"

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)

    # Serve the app with SSL
    serve(app, host="0.0.0.0", port=443, ssl=context)
    #app.run(debug=True)