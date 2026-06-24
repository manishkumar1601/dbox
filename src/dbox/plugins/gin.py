from __future__ import annotations

from dbox.plugins.base import DetectionRule, FrameworkPlugin


class GinPlugin(FrameworkPlugin):
    name = "gin"
    label = "Gin"
    runtime = "go"
    document_root = "/"
    priority = 80
    detection = DetectionRule(
        go_modules=("github.com/gin-gonic/gin",),
    )

    def commands(self) -> dict[str, list[str]]:
        return {"go": ["go"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            f"test -f go.mod || go mod init {project_name}",
            "test -f main.go || cat > main.go <<'EOF'\n"
            "package main\n\n"
            "import \"github.com/gin-gonic/gin\"\n\n"
            "func main() {\n"
            "    r := gin.Default()\n"
            "    r.GET(\"/\", func(c *gin.Context) {\n"
            "        c.JSON(200, gin.H{\"hello\": \"from dbox (Gin)\"})\n"
            "    })\n"
            "    r.Run(\":8080\")\n"
            "}\n"
            "EOF",
            "go get github.com/gin-gonic/gin",
            "go mod tidy",
        ]

    def app_env(self, db) -> dict[str, str]:
        if db.engine == "sqlite":
            return {}
        driver = "postgres" if db.engine == "postgres" else "mysql"
        port = 5432 if db.engine == "postgres" else 3306
        # Common convention for Go apps using gorm / sqlx.
        return {
            "DB_DRIVER": driver,
            "DB_HOST": "db",
            "DB_PORT": str(port),
            "DB_NAME": db.name,
            "DB_USER": db.user,
            "DB_PASSWORD": db.password,
        }

    def post_create_note(self) -> str | None:
        return "Edit main.go to add routes. `air` watches the project and auto-rebuilds."
