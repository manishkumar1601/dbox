from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


class LaravelPlugin(FrameworkPlugin):
    name = "laravel"
    label = "Laravel"
    document_root = "/public"
    priority = 80
    detection = DetectionRule(
        files=("artisan",),
        any_files=("bootstrap/app.php", "routes/web.php"),
        composer=("laravel/framework",),
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "gd", "zip", "intl", "bcmath", "exif", "opcache"]

    def services(self) -> list[str]:
        return ["redis", "mailpit"]

    def commands(self) -> dict[str, list[str]]:
        return {"artisan": ["php", "artisan"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project laravel/laravel /tmp/app --no-interaction --prefer-dist",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
        ]
