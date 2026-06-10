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
        return ["mailpit", "phpmyadmin"]

    def commands(self) -> dict[str, list[str]]:
        return {"artisan": ["php", "artisan"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project laravel/laravel /tmp/app --no-interaction --prefer-dist",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
            # storage/ and bootstrap/cache must be writable by the web server
            # user (www-data); without this Laravel can't write logs or compiled
            # views and dies with a tempnam()/UnexpectedValueException.
            "chmod -R 777 storage bootstrap/cache",
        ]
