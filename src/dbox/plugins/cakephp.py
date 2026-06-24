from __future__ import annotations

from dbox.plugins.base import DetectionRule, FrameworkPlugin


class CakePhpPlugin(FrameworkPlugin):
    name = "cakephp"
    label = "CakePHP"
    document_root = "/webroot"
    priority = 75
    detection = DetectionRule(
        files=("bin/cake",),
        any_files=("config/app.php", "src/Application.php"),
        composer=("cakephp/cakephp",),
    )

    def extensions(self) -> list[str]:
        # pdo_sqlite is used by DebugKit's storage in development.
        return ["pdo_mysql", "pdo_sqlite", "intl", "mbstring", "opcache"]

    def commands(self) -> dict[str, list[str]]:
        return {"cake": ["bin/cake"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project cakephp/app /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
            "chmod -R 777 tmp logs 2>/dev/null || true",  # must be writable
        ]

    def app_env(self, db) -> dict[str, str]:
        if db.engine == "sqlite":
            return {}
        scheme = "postgres" if db.engine == "postgres" else "mysql"
        port = 5432 if db.engine == "postgres" else 3306
        # app_local.php reads `env('DATABASE_URL')`, which overrides host/creds.
        return {"DATABASE_URL": f"{scheme}://{db.user}:{db.password}@db:{port}/{db.name}"}
