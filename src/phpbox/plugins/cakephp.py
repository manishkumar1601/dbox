from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


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
        return ["pdo_mysql", "intl", "mbstring", "opcache"]

    def commands(self) -> dict[str, list[str]]:
        return {"cake": ["bin/cake"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project cakephp/app /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
        ]
