from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


class LaminasPlugin(FrameworkPlugin):
    name = "laminas"
    label = "Laminas"
    document_root = "/public"
    priority = 60
    detection = DetectionRule(
        any_files=("config/modules.config.php",),
        composer=("laminas/laminas-mvc", "laminas/laminas-component-installer"),
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "intl", "opcache"]

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project laminas/laminas-mvc-skeleton /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
        ]
