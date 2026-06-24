from __future__ import annotations

from dbox.plugins.base import DetectionRule, FrameworkPlugin


class SymfonyPlugin(FrameworkPlugin):
    name = "symfony"
    label = "Symfony"
    document_root = "/public"
    priority = 80
    detection = DetectionRule(
        files=("bin/console",),
        any_files=("config/bundles.php", "src/Kernel.php"),
        composer=("symfony/framework-bundle", "symfony/flex"),
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "intl", "zip", "opcache", "xml"]

    def services(self) -> list[str]:
        return ["mailpit", "phpmyadmin"]

    def commands(self) -> dict[str, list[str]]:
        return {"console": ["php", "bin/console"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project symfony/skeleton /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
            "composer --working-dir=/var/www/html require webapp --no-interaction || true",
            "chmod -R 777 var 2>/dev/null || true",  # cache/logs must be writable
        ]

    def app_env(self, db) -> dict[str, str]:
        if db.engine == "sqlite":
            return {}
        driver = "postgresql" if db.engine == "postgres" else "mysql"
        port = 5432 if db.engine == "postgres" else 3306
        # Symfony reads DATABASE_URL; a real env var overrides the .env value.
        return {"DATABASE_URL": f"{driver}://{db.user}:{db.password}@db:{port}/{db.name}"}
