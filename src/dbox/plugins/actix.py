from __future__ import annotations

from dbox.plugins.base import DetectionRule, FrameworkPlugin


class ActixPlugin(FrameworkPlugin):
    name = "actix"
    label = "Actix-web"
    runtime = "rust"
    document_root = "/"
    priority = 80
    detection = DetectionRule(cargo_crates=("actix-web",))

    def commands(self) -> dict[str, list[str]]:
        return {"cargo": ["cargo"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            f"test -f Cargo.toml || cargo init --name {project_name} --bin .",
            # cargo add was stabilised in Rust 1.62 — bake in actix-web + tokio.
            "grep -q '^actix-web' Cargo.toml || cargo add actix-web@4",
            "cat > src/main.rs <<'EOF'\n"
            "use actix_web::{get, App, HttpServer, Responder};\n\n"
            "#[get(\"/\")]\n"
            "async fn hello() -> impl Responder { \"hello from dbox (Actix-web)\" }\n\n"
            "#[actix_web::main]\n"
            "async fn main() -> std::io::Result<()> {\n"
            "    HttpServer::new(|| App::new().service(hello))\n"
            "        .bind((\"0.0.0.0\", 8080))?\n"
            "        .run()\n"
            "        .await\n"
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

    def post_create_note(self) -> str | None:
        return "Edit src/main.rs to add handlers. `cargo-watch` rebuilds on save."
