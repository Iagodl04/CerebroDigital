<?php
$CONFIG = array (
  'htaccess.RewriteBase' => '/',
  'memcache.local' => '\\OC\\Memcache\\APCu',
  'apps_paths' => 
  array (
    0 => 
    array (
      'path' => '/var/www/html/apps',
      'url' => '/apps',
      'writable' => false,
    ),
    1 => 
    array (
      'path' => '/var/www/html/custom_apps',
      'url' => '/custom_apps',
      'writable' => true,
    ),
  ),
  'upgrade.disable-web' => true,
  'instanceid' => 'ocgnu0pw99mk',
  'passwordsalt' => 'u4xJanfLjOYJk+yRLq5dAY9tEUoTT8',
  'secret' => 'O28SJzhSm/QXEXgZS0TpB1/XiKKiskPOa1DFBy5ivnL5GC8z',
  'trusted_domains' => 
  array (
    0 => '192.168.1.10:8082',
  ),
  'datadirectory' => '/var/www/html/data',
  'dbtype' => 'sqlite3',
  'version' => '32.0.1.2',
  'overwrite.cli.url' => 'http://192.168.1.10:8082',
  'installed' => true,
  'maintenance' => false,
);
