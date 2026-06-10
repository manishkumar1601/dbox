from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


class SlimPlugin(FrameworkPlugin):
    name = "slim"
    label = "Slim"
    document_root = "/public"
    priority = 60
    # public/index.php is too generic to match on alone — require the package.
    detection = DetectionRule(
        composer=("slim/slim",),
    )

    def extensions(self) -> list[str]:
        return ["opcache", "curl"]

    def create_steps(self, project_name: str) -> list[str]:
        return [
            "composer create-project slim/slim-skeleton /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
        ]
