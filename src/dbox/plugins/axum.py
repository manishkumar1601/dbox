from __future__ import annotations

from dbox.plugins.base import DetectionRule, FrameworkPlugin


class AxumPlugin(FrameworkPlugin):
    name = "axum"
    label = "Axum"
    runtime = "rust"
    document_root = "/"
    priority = 80
    detection = DetectionRule(cargo_crates=("axum",))

    def commands(self) -> dict[str, list[str]]:
        return {"cargo": ["cargo"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            f"test -f Cargo.toml || cargo init --name {project_name} --bin .",
            "grep -q '^axum' Cargo.toml || cargo add axum",
            "grep -q '^tokio' Cargo.toml || cargo add tokio --features full",
            "cat > src/main.rs <<'EOF'\n"
            "use axum::{routing::get, Router};\n\n"
            "#[tokio::main]\n"
            "async fn main() {\n"
            "    let app = Router::new().route(\"/\", get(|| async { \"hello from dbox (Axum)\" }));\n"
            "    let listener = tokio::net::TcpListener::bind(\"0.0.0.0:8080\").await.unwrap();\n"
            "    axum::serve(listener, app).await.unwrap();\n"
            "}\n"
            "EOF",
        ]

    def app_env(self, db) -> dict[str, str]:
        if db.engine == "sqlite":
            return {}
        scheme = "postgres" if db.engine == "postgres" else "mysql"
        port = 5432 if db.engine == "postgres" else 3306
        return {
            "DATABASE_URL": f"{scheme}://{db.user}:{db.password}@db:{port}/{db.name}",
        }
