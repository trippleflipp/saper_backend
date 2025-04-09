from app import create_app, db
from waitress import serve

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    #app.run(debug=True)
    serve(app, host="0.0.0.0", port=443, ssl_cert="ssl_cert.pem", ssl_key="ssl_key.pem")