from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


class WordPressPlugin(FrameworkPlugin):
    name = "wordpress"
    label = "WordPress"
    document_root = "/"
    priority = 85
    detection = DetectionRule(
        any_files=("wp-config.php", "wp-load.php", "wp-content/"),
    )

    def extensions(self) -> list[str]:
        # WordPress core talks to MySQL via the mysqli extension (not PDO).
        return ["mysqli", "pdo_mysql", "gd", "exif", "intl", "zip", "imagick", "opcache"]

    def services(self) -> list[str]:
        return ["phpmyadmin", "mailpit"]

    def commands(self) -> dict[str, list[str]]:
        # wp-cli is installed in the image; allow-root for container usage.
        return {"wp": ["wp", "--allow-root"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "wp core download --allow-root --path=/var/www/html",
        ]
