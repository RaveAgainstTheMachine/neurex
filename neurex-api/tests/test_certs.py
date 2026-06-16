from core.security.certs import generate_self_signed_cert


def test_generate_self_signed_cert(tmp_path):
    cert_dir = tmp_path / "certs"
    cert_path, key_path = generate_self_signed_cert(cert_dir)
    
    assert cert_path.exists()
    assert key_path.exists()
    assert cert_path.name == "cert.pem"
    assert key_path.name == "key.pem"
    
    # Read files to make sure they are PEM-encoded
    cert_content = cert_path.read_text()
    key_content = key_path.read_text()
    
    assert "BEGIN CERTIFICATE" in cert_content
    assert "BEGIN RSA PRIVATE KEY" in key_content

    # Call again, should return existing and not overwrite/regenerate
    orig_mtime_cert = cert_path.stat().st_mtime
    cert_path2, key_path2 = generate_self_signed_cert(cert_dir)
    assert cert_path2 == cert_path
    assert key_path2 == key_path
    assert cert_path2.stat().st_mtime == orig_mtime_cert
