from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


class YiiPlugin(FrameworkPlugin):
    name = "yii"
    label = "Yii"
    document_root = "/web"
    priority = 75
    detection = DetectionRule(
        files=("yii",),
        any_files=("config/web.php", "runtime/"),
        composer=("yiisoft/yii2",),
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "intl", "gd", "opcache"]

    def commands(self) -> dict[str, list[str]]:
        return {"yii": ["php", "yii"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project yiisoft/yii2-app-basic /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
            "chmod -R 777 runtime web/assets 2>/dev/null || true",  # must be writable
        ]
