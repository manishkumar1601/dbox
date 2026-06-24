from __future__ import annotations

from dbox.plugins.base import DetectionRule, FrameworkPlugin


class RustPlugin(FrameworkPlugin):
    """Plain Rust runtime — fallback for any project with a Cargo.toml."""

    name = "rust"
    label = "Rust"
    runtime = "rust"
    document_root = "/"
    priority = 1
    detection = DetectionRule(any_files=("Cargo.toml",))

    def commands(self) -> dict[str, list[str]]:
        return {"cargo": ["cargo"]}

    def create_steps(self, project_name: str) -> list[str]:
        return [
            f"test -f Cargo.toml || cargo init --name {project_name} --bin .",
            # Provide a minimal HTTP server using std (no extra deps).
            "test -s src/main.rs || cat > src/main.rs <<'EOF'\n"
            "use std::io::{Read, Write};\n"
            "use std::net::TcpListener;\n\n"
            "fn main() {\n"
            "    let listener = TcpListener::bind(\"0.0.0.0:8080\").unwrap();\n"
            "    println!(\"listening on :8080\");\n"
            "    for stream in listener.incoming() {\n"
            "        if let Ok(mut s) = stream {\n"
            "            let mut buf = [0u8; 1024];\n"
            "            let _ = s.read(&mut buf);\n"
            "            let body = \"hello from dbox (Rust)\";\n"
            "            let response = format!(\n"
            "                \"HTTP/1.1 200 OK\\r\\nContent-Length: {}\\r\\nContent-Type: text/plain\\r\\n\\r\\n{}\",\n"
            "                body.len(), body);\n"
            "            let _ = s.write_all(response.as_bytes());\n"
            "        }\n"
            "    }\n"
            "}\n"
            "EOF",
        ]
