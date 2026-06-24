from __future__ import annotations

import json

from dbox.plugins.base import Credential, DetectionRule, FrameworkPlugin


class MagentoPlugin(FrameworkPlugin):
    name = "magento"
    label = "Magento"
    document_root = "/pub"
    priority = 78
    detection = DetectionRule(
        files=("bin/magento",),
        any_files=("app/etc/env.php", "app/etc/config.php"),
        composer=("magento/product-community-edition",),
    )

    def extensions(self) -> list[str]:
        return [
            "pdo_mysql",
            "bcmath",
            "gd",
            "intl",
            "mbstring",
            "soap",
            "sockets",
            "sodium",
            "xml",
            "xsl",
            "zip",
            "opcache",
        ]

    def services(self) -> list[str]:
        return ["elasticsearch", "phpmyadmin"]

    def commands(self) -> dict[str, list[str]]:
        return {"magento": ["php", "bin/magento"]}

    # ---- scaffolding ---------------------------------------------------

    def create_credentials(self) -> list[Credential]:
        # Magento's Composer repository requires authenticated access keys,
        # generated at https://commercemarketplace.adobe.com → My Profile →
        # Access Keys. The public key is the username, the private key the
        # password.
        return [
            Credential("MAGENTO_PUBLIC_KEY", "Magento Marketplace public key", secret=False),
            Credential("MAGENTO_PRIVATE_KEY", "Magento Marketplace private key", secret=True),
        ]

    def create_env(self, credentials: dict[str, str]) -> dict[str, str]:
        auth = {
            "http-basic": {
                "repo.magento.com": {
                    "username": credentials.get("MAGENTO_PUBLIC_KEY", ""),
                    "password": credentials.get("MAGENTO_PRIVATE_KEY", ""),
                }
            }
        }
        # Composer reads COMPOSER_AUTH automatically — no auth.json needed.
        return {"COMPOSER_AUTH": json.dumps(auth)}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project --repository-url=https://repo.magento.com/ "
            "magento/project-community-edition /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
            "chmod +x /var/www/html/bin/magento || true",
        ]

    def post_create_note(self) -> str | None:
        return (
            "Code installed. Finish the install once containers are up\n"
            "(db-name is your project name; root / root always works as the DB login):\n"
            "    dbox magento setup:install \\\n"
            "      --base-url=http://localhost --db-host=db --db-name=<project> \\\n"
            "      --db-user=root --db-password=root \\\n"
            "      --search-engine=elasticsearch7 --elasticsearch-host=elasticsearch \\\n"
            "      --admin-firstname=Admin --admin-lastname=User \\\n"
            "      --admin-email=admin@example.com --admin-user=admin --admin-password=Admin123!"
        )
