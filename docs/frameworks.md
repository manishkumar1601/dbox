# Frameworks

PHPBox supports 9 frameworks and 4 CMS platforms. Each is implemented as a
plugin in `src/phpbox/plugins/` describing how to detect it, what it needs, how
to scaffold it, and which native CLI it exposes.

## Supported

| Name (`phpbox create <name>`) | Label | Document root | Native CLI |
|---|---|---|---|
| `laravel` | Laravel | `/public` | `phpbox artisan` |
| `symfony` | Symfony | `/public` | `phpbox console` |
| `codeigniter` | CodeIgniter 4 | `/public` | `phpbox spark` |
| `codeigniter3` | CodeIgniter 3 | `/` | — |
| `cakephp` | CakePHP | `/webroot` | `phpbox cake` |
| `yii` | Yii | `/web` | `phpbox yii` |
| `slim` | Slim | `/public` | — |
| `laminas` | Laminas | `/public` | — |
| `corephp` | Core PHP | `/` | — |
| `wordpress` | WordPress | `/` | `phpbox wp` |
| `drupal` | Drupal | `/web` | `phpbox drush` |
| `magento` | Magento | `/pub` | `phpbox magento` |
| `joomla` | Joomla | `/` | `phpbox joomla` |

## Default services per framework

`phpbox create`/`init` enable a sensible set of companion services per
framework (toggle any afterwards — see [services.md](services.md)):

| Framework | Mailpit | phpMyAdmin | Elasticsearch | Redis |
|---|:---:|:---:|:---:|:---:|
| Laravel | ✅ | ✅ | | |
| Symfony | ✅ | ✅ | | |
| CodeIgniter 3 & 4 | ✅ | ✅ | | |
| WordPress | ✅ | ✅ | | |
| Core PHP | ✅ | ✅ | | |
| Magento | | ✅ | ✅ | |
| CakePHP, Yii, Slim, Laminas, Drupal, Joomla | | | | |

**Redis is off by default everywhere** — enable per project with
`phpbox redis enable`. Every framework also gets a **MariaDB** database (unless
you switch to SQLite), with credentials matching the project name plus a
`root` / `root` admin login (see [databases.md](databases.md)).

## Notes on specific frameworks

* **WordPress** — needs the `mysqli` extension (not just PDO); PHPBox enables it
  automatically. WordPress installs WP-CLI into the image (`phpbox wp …`).
* **CodeIgniter 3** — CI 3.1.x isn't clean on PHP 8.2+ (it emits "dynamic
  property deprecated" notices), so PHPBox defaults CI3 projects to **PHP 8.1**.
  Switch any project's PHP with `phpbox php use <version>`.

## How detection works

`phpbox init` / `phpbox detect` run every plugin's detection rules and pick the
highest-`priority` match. A plugin matches if **any** of these is true:

* a required set of **files** all exist, or
* **any** of a set of marker files exists, or
* `composer.json` requires one of the plugin's **packages**.

When several match (e.g. CodeIgniter 4 markers also satisfy CodeIgniter 3), the
higher `priority` wins.

| Framework | Detection markers | composer.json require |
|---|---|---|
| Laravel | `artisan` (+ `bootstrap/app.php` or `routes/web.php`) | `laravel/framework` |
| Symfony | `bin/console` (+ `config/bundles.php` or `src/Kernel.php`) | `symfony/framework-bundle`, `symfony/flex` |
| CodeIgniter 4 | `spark` (+ `app/Config/App.php`) | `codeigniter4/framework` |
| CodeIgniter 3 | `application/config/config.php` + `system/core/CodeIgniter.php` | — |
| CakePHP | `bin/cake` | `cakephp/cakephp` |
| Yii | `yii` | `yiisoft/yii2` |
| Slim | — | `slim/slim` |
| Laminas | `config/modules.config.php` | `laminas/laminas-mvc` |
| WordPress | `wp-config.php`, `wp-load.php`, or `wp-content/` | — |
| Drupal | `core/lib/Drupal.php` or `sites/default/settings.php` | `drupal/core` |
| Magento | `bin/magento` | `magento/product-community-edition` |
| Joomla | `configuration.php` or `libraries/src/Factory.php` | — |
| Core PHP | `index.php` (lowest priority fallback) | — |

PHP version is additionally inferred from the `php` constraint in
`composer.json`; extensions from framework defaults plus any `ext-*` requires.

## Scaffolding (`phpbox create`)

Most frameworks scaffold via `composer create-project` run inside the PHP
container, so the result lands in your project on the host:

| Framework | Scaffolding source |
|---|---|
| Laravel | `composer create-project laravel/laravel` |
| Symfony | `composer create-project symfony/skeleton` + `composer require webapp` |
| CodeIgniter 4 | `composer create-project codeigniter4/appstarter` |
| CakePHP | `composer create-project cakephp/app` |
| Yii | `composer create-project yiisoft/yii2-app-basic` |
| Slim | `composer create-project slim/slim-skeleton` |
| Laminas | `composer create-project laminas/laminas-mvc-skeleton` |
| Drupal | `composer create-project drupal/recommended-project` + Drush |
| WordPress | `wp core download` (WP-CLI is baked into the image) |
| CodeIgniter 3 | downloads the official release tarball |
| Joomla | downloads the official release tarball |
| Core PHP | writes a starter `index.php` |
| Magento | `composer create-project … magento/project-community-edition` (see below) |

## Magento

Magento's Composer repository (`repo.magento.com`) requires **authenticated
access keys**, generated at *Adobe Commerce Marketplace → My Profile → Access
Keys*. The public key is the username, the private key the password.

`phpbox create magento shop` will:

1. Prompt for the keys — or read `MAGENTO_PUBLIC_KEY` / `MAGENTO_PRIVATE_KEY`
   from the environment (useful in CI):

   ```bash
   export MAGENTO_PUBLIC_KEY=xxxxxxxx
   export MAGENTO_PRIVATE_KEY=yyyyyyyy
   phpbox create magento shop
   ```

2. Inject them as a `COMPOSER_AUTH` environment variable into the scaffolding
   container (no `auth.json` is written to disk).
3. Run `composer create-project … magento/project-community-edition`.
4. Print the `setup:install` command to finish the install once the database
   and Elasticsearch containers are up:

   ```bash
   # db-name is your project name; root / root always works as the DB login
   phpbox magento setup:install \
     --base-url=http://localhost --db-host=db --db-name=<project> \
     --db-user=root --db-password=root \
     --search-engine=elasticsearch7 --elasticsearch-host=elasticsearch \
     --admin-firstname=Admin --admin-lastname=User \
     --admin-email=admin@example.com --admin-user=admin --admin-password=Admin123!
   ```

Magento enables Elasticsearch and phpMyAdmin by default and installs the full
extension set it requires (`bcmath`, `gd`, `intl`, `mbstring`, `soap`,
`sockets`, `sodium`, `xml`, `xsl`, `zip`, `pdo_mysql`, `opcache`).

## Adding your own framework

See [plugins.md](plugins.md).
