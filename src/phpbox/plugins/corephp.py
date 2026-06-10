from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


class CorePhpPlugin(FrameworkPlugin):
    """Fallback for plain PHP projects with no recognised framework."""

    name = "corephp"
    label = "Core PHP"
    document_root = "/"
    priority = 1  # lowest — only wins when nothing else matches
    detection = DetectionRule(any_files=("index.php",))

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "opcache"]

    def services(self) -> list[str]:
        return ["phpmyadmin", "mailpit"]

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "test -f /var/www/html/index.php || "
            "printf '<?php\\nphpinfo();\\n' > /var/www/html/index.php",
        ]
