from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


class CodeIgniter4Plugin(FrameworkPlugin):
    name = "codeigniter"
    label = "CodeIgniter 4"
    document_root = "/public"
    priority = 75
    detection = DetectionRule(
        files=("spark",),
        any_files=("app/Config/App.php",),
        composer=("codeigniter4/framework",),
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "intl", "curl", "gd", "opcache"]

    def services(self) -> list[str]:
        return ["phpmyadmin", "mailpit"]

    def commands(self) -> dict[str, list[str]]:
        return {"spark": ["php", "spark"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project codeigniter4/appstarter /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
            "chmod -R 777 writable 2>/dev/null || true",  # must be writable
        ]

    def app_env(self, db) -> dict[str, str]:
        if db.engine == "sqlite":
            return {}
        dbdriver = "Postgre" if db.engine == "postgres" else "MySQLi"
        port = 5432 if db.engine == "postgres" else 3306
        # CI4 reads these dotted keys from the environment.
        return {
            "database.default.hostname": "db",
            "database.default.database": db.name,
            "database.default.username": db.user,
            "database.default.password": db.password,
            "database.default.DBDriver": dbdriver,
            "database.default.port": str(port),
        }
