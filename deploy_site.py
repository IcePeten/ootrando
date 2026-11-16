import ftplib
import os
from pathlib import Path

import build_site

ROOT = Path(__file__).resolve().parent


def load_env():
    env = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if k.startswith("FTP_")})
    return env


def main():
    env = load_env()
    build_site.main(force_https=env.get("FORCE_HTTPS", "").lower() in ("1", "true", "yes"))
    ftp = ftplib.FTP_TLS()
    ftp.connect(env["FTP_HOST"], int(env.get("FTP_PORT", 21)), timeout=60)
    ftp.login(env["FTP_USERNAME"], env["FTP_PASSWORD"])
    ftp.prot_p()
    ftp.set_pasv(True)
    remote = env.get("FTP_DIR", "/")
    ftp.cwd(remote)
    for path in sorted(build_site.OUT.iterdir()):
        with open(path, "rb") as f:
            ftp.storbinary(f"STOR {path.name}", f)
        print(f"uploaded {path.name} ({path.stat().st_size:,} bytes)")
    listing = []
    ftp.retrlines("LIST -a", listing.append)
    ftp.quit()
    print("\n".join(listing))


if __name__ == "__main__":
    main()
