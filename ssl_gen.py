from OpenSSL import crypto
from socket import gethostname
from os.path import exists

def generate_self_signed_cert(cert_path, key_path, hostname=gethostname()):
    """
    Создает самозаверенный SSL-сертификат и приватный ключ.
    """
    if exists(cert_path) and exists(key_path):
        print(f"Сертификат и ключ уже существуют: {cert_path}, {key_path}")
        return

    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)  # Generate key

    cert = crypto.X509()
    cert.get_subject().C = "RU"  #  Код страны (RU)
    cert.get_subject().O = "Saper" #  Название организации
    cert.get_subject().CN = hostname #  Имя хоста (доменное имя или localhost)
    cert.set_serial_number(1000)  #  Серийный номер
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(31536000) # Срок действия: 1 год
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')

    with open(cert_path, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open(key_path, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

cert_file = "ssl_cert.pem"
key_file = "ssl_key.pem"

generate_self_signed_cert(cert_file, key_file)
print(f"Сгенерирован самозаверенный сертификат: {cert_file}")
print(f"Сгенерирован приватный ключ: {key_file}")