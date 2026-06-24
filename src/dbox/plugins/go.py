from __future__ import annotations

from dbox.plugins.base import DetectionRule, FrameworkPlugin


class GoPlugin(FrameworkPlugin):
    """Plain Go (net/http) runtime — fallback for any project with a go.mod."""

    name = "go"
    label = "Go"
    runtime = "go"
    document_root = "/"
    priority = 1  # lowest — framework-specific Go plugins win the tie
    detection = DetectionRule(any_files=("go.mod",))

    def create_steps(self, project_name: str) -> list[str]:
        return [
            f"test -f go.mod || go mod init {project_name}",
            "test -f main.go || cat > main.go <<'EOF'\n"
            "package main\n\n"
            "import (\n"
            "    \"fmt\"\n"
            "    \"net/http\"\n"
            ")\n\n"
            "func main() {\n"
            "    http.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n"
            "        fmt.Fprintln(w, \"hello from dbox (Go)\")\n"
            "    })\n"
            "    http.ListenAndServe(\":8080\", nil)\n"
            "}\n"
            "EOF",
            "go mod tidy",
        ]
