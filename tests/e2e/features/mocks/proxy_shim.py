"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import socket
import ssl
import tempfile
import threading
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_adhoc_cert():
    """Generates a self-signed cert and returns the path to a temp file."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Create mocked hostname based on mock OCI config from environment.py
    region = os.getenv("MOCK_REGION", "us-ashburn-1")
    hostname = f"iaas.{region}.oraclecloud.com"

    print(f"Generating SSL Cert for: {hostname}")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(hostname)]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    # Write private key and cert to a temporary file
    tmp_cert = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    tmp_cert.write(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    tmp_cert.write(cert.public_bytes(serialization.Encoding.PEM))
    tmp_cert.close()
    return tmp_cert.name


# Global path for the certificate
CERT_PATH = generate_adhoc_cert()


def pipe(src, dst):
    """Continuously shuffles bytes from src to dst."""
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass


def handle_client(client_sock):
    target_sock = None
    try:
        # Intercept the request
        raw_request = client_sock.recv(4096)
        request_lines = raw_request.decode("utf-8", errors="ignore").split("\r\n")
        if request_lines and len(request_lines) > 0:
            first_line = request_lines[0]
            if first_line.startswith("GET /health "):
                # Health check response
                response = b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 19\r\n\r\n{"status": "healthy"}'  # noqa
                client_sock.sendall(response)
                return
            elif b"CONNECT" in raw_request:
                # Tell the client the tunnel is ready
                client_sock.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

                # Wrap the socket with SSL (Terminate SSL here)
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(certfile=CERT_PATH)

                try:
                    ssock = context.wrap_socket(client_sock, server_side=True)
                except ssl.SSLError as e:
                    print(f"SSL Handshake Failed: {e}")
                    return

                # Connect to the local Plain HTTP Flask Mock
                target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_sock.connect(("127.0.0.1", 5001))

                # Create threads for bidirectional traffic
                t1 = threading.Thread(target=pipe, args=(ssock, target_sock), daemon=True)
                t2 = threading.Thread(target=pipe, args=(target_sock, ssock), daemon=True)

                t1.start()
                t2.start()

                # Keep the connection alive until the threads finish or timeout
                t1.join(timeout=30)
                t2.join(timeout=30)
            else:
                # For other requests, perhaps close or handle minimally
                client_sock.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
    except Exception as e:
        print(f"Shim Client Error: {e}")
    finally:
        if target_sock:
            try:
                target_sock.close()
            except Exception:
                pass
        try:
            client_sock.close()
        except Exception:
            pass


def main():
    print("--- Proxy Shim Starting ---")
    print(f"Generated Adhoc Cert: {CERT_PATH}")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(("127.0.0.1", 5000))
        server.listen(20)
        print("Listening on 127.0.0.1:5000 (Terminating SSL, piping to 5001)")

        while True:
            conn, _ = server.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down Shim...")
    finally:
        server.close()
        if os.path.exists(CERT_PATH):
            os.remove(CERT_PATH)


if __name__ == "__main__":
    main()
