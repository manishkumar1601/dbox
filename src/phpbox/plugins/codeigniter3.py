from __future__ import annotations

from phpbox.plugins.base import DetectionRule, FrameworkPlugin


class CodeIgniter3Plugin(FrameworkPlugin):
    name = "codeigniter3"
    label = "CodeIgniter 3"
    document_root = "/"
    priority = 40  # lower: CI4 markers are more specific, check it first
    detection = DetectionRule(
        files=("application/config/config.php", "system/core/CodeIgniter.php"),
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "curl", "gd"]

    def services(self) -> list[str]:
        return ["phpmyadmin", "mailpit"]

    def create_steps(self, project_name: str) -> list[str]:
        # CI3 ships as a downloadable archive (no first-party composer starter).
        return [
            "curl -fsSL https://github.com/bcit-ci/CodeIgniter/archive/refs/tags/3.1.13.tar.gz -o /tmp/ci3.tgz",
            "mkdir -p /tmp/app && tar -xzf /tmp/ci3.tgz -C /tmp/app --strip-components=1",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app /tmp/ci3.tgz",
        ]
