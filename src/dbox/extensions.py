"""PHP extension metadata.

Maps each supported extension to how it is installed inside the PHP container:

* ``core``  — built with ``docker-php-ext-install`` (optionally configured first)
* ``pecl``  — installed via ``pecl install`` then ``docker-php-ext-enable``
* ``builtin`` — already present in the official image, nothing to do

``apt`` lists the Debian system packages required to build the extension.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Extension:
    name: str
    kind: str  # "core" | "pecl" | "builtin"
    apt: tuple[str, ...] = ()
    configure: str = ""  # docker-php-ext-configure flags


EXTENSIONS: dict[str, Extension] = {
    # --- core extensions (docker-php-ext-install) ---
    "gd": Extension(
        "gd",
        "core",
        apt=("libfreetype6-dev", "libjpeg62-turbo-dev", "libpng-dev"),
        configure="--with-freetype --with-jpeg",
    ),
    "intl": Extension("intl", "core", apt=("libicu-dev",)),
    "zip": Extension("zip", "core", apt=("libzip-dev",)),
    "soap": Extension("soap", "core", apt=("libxml2-dev",)),
    "ldap": Extension("ldap", "core", apt=("libldap2-dev",)),
    "bcmath": Extension("bcmath", "core"),
    "exif": Extension("exif", "core"),
    "sockets": Extension("sockets", "core"),
    "opcache": Extension("opcache", "core"),
    "mysqli": Extension("mysqli", "core"),
    "pdo_mysql": Extension("pdo_mysql", "core"),
    "pdo_pgsql": Extension("pdo_pgsql", "core", apt=("libpq-dev",)),
    "pgsql": Extension("pgsql", "core", apt=("libpq-dev",)),
    "xml": Extension("xml", "core", apt=("libxml2-dev",)),
    "sodium": Extension("sodium", "core", apt=("libsodium-dev",)),
    "mbstring": Extension("mbstring", "core", apt=("libonig-dev",)),
    "xsl": Extension("xsl", "core", apt=("libxslt1-dev",)),
    "curl": Extension("curl", "builtin"),
    # --- PECL extensions ---
    "redis": Extension("redis", "pecl"),
    "imagick": Extension("imagick", "pecl", apt=("libmagickwand-dev",)),
    "mongodb": Extension("mongodb", "pecl"),
    "xdebug": Extension("xdebug", "pecl"),
}


def resolve(names: list[str]) -> dict:
    """Group the requested extensions into the buckets the Dockerfile needs.

    Unknown extensions are passed through as ``core`` installs (covers "all
    official PHP extensions" — if the image can't build it, the build fails
    loudly rather than silently dropping it).
    """
    apt: set[str] = set()
    configure: list[Extension] = []
    core: list[str] = []
    pecl: list[str] = []

    for name in names:
        ext = EXTENSIONS.get(name)
        if ext is None:
            # Unknown but possibly valid official extension.
            core.append(name)
            continue
        apt.update(ext.apt)
        if ext.kind == "builtin":
            continue
        if ext.kind == "pecl":
            pecl.append(ext.name)
        else:
            if ext.configure:
                configure.append(ext)
            core.append(ext.name)

    return {
        "apt": sorted(apt),
        "configure": configure,
        "core": core,
        "pecl": pecl,
    }


def supported() -> list[str]:
    return sorted(EXTENSIONS.keys())
