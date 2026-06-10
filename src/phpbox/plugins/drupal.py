from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


class DrupalPlugin(FrameworkPlugin):
    name = "drupal"
    label = "Drupal"
    document_root = "/web"
    priority = 78
    detection = DetectionRule(
        any_files=("core/lib/Drupal.php", "sites/default/settings.php"),
        composer=("drupal/core", "drupal/core-recommended"),
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "pdo_pgsql", "gd", "intl", "zip", "opcache"]

    def commands(self) -> dict[str, list[str]]:
        return {"drush": ["vendor/bin/drush"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project drupal/recommended-project /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
            "composer --working-dir=/var/www/html require drush/drush --no-interaction || true",
        ]
