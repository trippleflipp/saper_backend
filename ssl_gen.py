from OpenSSL import crypto
from socket import gethostname
from os.path import exists

def generate_self_signed_cert(cert_path, key_path, hostname=gethostname()):
    """
    Creates a self-signed SSL certificate and private key.
    """
    if exists(cert_path) and exists(key_path):
        print(f"Certificate and key already exist: {cert_path}, {key_path}")
        return

    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)  # Generate key

    cert = crypto.X509()
    cert.get_subject().C = "RU"  # Country Code (RU)
    cert.get_subject().O = "Saper"  # Organization Name
    cert.get_subject().CN = hostname  # Hostname (domain name or localhost)
    cert.set_serial_number(1000)  # Serial Number
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(31536000)  # Validity: 1 year
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
print(f"Generated self-signed certificate: {cert_file}")
print(f"Generated private key: {key_file}")