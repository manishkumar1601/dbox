from __future__ import annotations

from dbox.plugins.base import DetectionRule, FrameworkPlugin


class JoomlaPlugin(FrameworkPlugin):
    name = "joomla"
    label = "Joomla"
    document_root = "/"
    priority = 78
    detection = DetectionRule(
        any_files=("configuration.php", "libraries/src/Factory.php"),
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "gd", "intl", "zip", "curl", "opcache"]

    def commands(self) -> dict[str, list[str]]:
        return {"joomla": ["php", "cli/joomla.php"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "curl -fsSL https://github.com/joomla/joomla-cms/releases/download/5.2.2/Joomla_5.2.2-Stable-Full_Package.tar.gz -o /tmp/joomla.tgz",
            "mkdir -p /tmp/app && tar -xzf /tmp/joomla.tgz -C /tmp/app",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app /tmp/joomla.tgz",
        ]
