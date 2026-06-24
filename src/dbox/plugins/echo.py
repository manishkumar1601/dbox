from __future__ import annotations

from dbox.plugins.base import DetectionRule, FrameworkPlugin


class EchoPlugin(FrameworkPlugin):
    name = "echo"
    label = "Echo"
    runtime = "go"
    document_root = "/"
    priority = 80
    detection = DetectionRule(
        go_modules=("github.com/labstack/echo/v4",),
    )

    def commands(self) -> dict[str, list[str]]:
        return {"go": ["go"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            f"test -f go.mod || go mod init {project_name}",
            "test -f main.go || cat > main.go <<'EOF'\n"
            "package main\n\n"
            "import (\n"
            "    \"net/http\"\n"
            "    \"github.com/labstack/echo/v4\"\n"
            ")\n\n"
            "func main() {\n"
            "    e := echo.New()\n"
            "    e.GET(\"/\", func(c echo.Context) error {\n"
            "        return c.JSON(http.StatusOK, map[string]string{\"hello\": \"from dbox (Echo)\"})\n"
            "    })\n"
            "    e.Logger.Fatal(e.Start(\":8080\"))\n"
            "}\n"
            "EOF",
            "go get github.com/labstack/echo/v4",
            "go mod tidy",
        ]

    def app_env(self, db) -> dict[str, str]:
        if db.engine == "sqlite":
            return {}
        driver = "postgres" if db.engine == "postgres" else "mysql"
        port = 5432 if db.engine == "postgres" else 3306
        return {
            "DB_DRIVER": driver,
            "DB_HOST": "db",
            "DB_PORT": str(port),
            "DB_NAME": db.name,
            "DB_USER": db.user,
            "DB_PASSWORD": db.password,
        }
