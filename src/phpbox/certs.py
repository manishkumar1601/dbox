"""Local TLS certificate generation for `phpbox ssl`.

Prefers `mkcert` (browser-trusted) when it's on the host PATH; otherwise falls
back to a self-signed certificate generated *inside the PHP container* using
PHP's built-in OpenSSL extension — so no host tooling (openssl/mkcert) is
required and it works identically on Windows, macOS, and Linux.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from phpbox import engine
from phpbox.config import PHPBOX_DIR, ProjectConfig

CERT_NAME = "cert.pem"
KEY_NAME = "key.pem"


def certs_dir(project_dir: Path) -> Path:
    return project_dir / PHPBOX_DIR / "certs"


def have_certs(project_dir: Path) -> bool:
    d = certs_dir(project_dir)
    return (d / CERT_NAME).exists() and (d / KEY_NAME).exists()


def _mkcert(project_dir: Path, host: str) -> bool:
    d = certs_dir(project_dir)
    try:
        subprocess.run(["mkcert", "-install"], check=False)
        result = subprocess.run(
            [
                "mkcert",
                "-cert-file", str(d / CERT_NAME),
                "-key-file", str(d / KEY_NAME),
                host, "localhost", "127.0.0.1", "::1",
            ],
            check=False,
        )
        return result.returncode == 0
    except OSError:
        return False


# PHP one-liner that writes a self-signed cert + key into the mounted certs dir.
_PHP_SELF_SIGNED = (
    'php -r \''
    '$d="/var/www/html/{phpbox}/certs";'
    '$dn=array("commonName"=>"{host}");'
    '$k=openssl_pkey_new(array("private_key_bits"=>2048,"private_key_type"=>OPENSSL_KEYTYPE_RSA));'
    '$csr=openssl_csr_new($dn,$k,array("digest_alg"=>"sha256"));'
    '$x=openssl_csr_sign($csr,null,$k,825,array("digest_alg"=>"sha256"));'
    'openssl_x509_export($x,$c);openssl_pkey_export($k,$p);'
    'file_put_contents("$d/cert.pem",$c);file_put_contents("$d/key.pem",$p);'
    'echo "ok";\''
)


def _self_signed(project_dir: Path, host: str) -> bool:
    # Needs the PHP image; build it if necessary.
    if engine.build(project_dir, "php") != 0:
        return False
    script = _PHP_SELF_SIGNED.format(phpbox=PHPBOX_DIR, host=host)
    engine.run_once(project_dir, script)
    return have_certs(project_dir)


def ensure(project_dir: Path, cfg: ProjectConfig) -> tuple[bool, str]:
    """Make sure cert.pem/key.pem exist. Returns (ok, method)."""
    if have_certs(project_dir):
        return True, "existing"
    d = certs_dir(project_dir)
    d.mkdir(parents=True, exist_ok=True)
    host = cfg.ssl.host or "localhost"

    if shutil.which("mkcert") and _mkcert(project_dir, host):
        return True, "mkcert (trusted)"

    if _self_signed(project_dir, host):
        return True, "self-signed"

    return False, "failed"
