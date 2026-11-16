<?php
$home = dirname($_SERVER['DOCUMENT_ROOT'] ?? __DIR__);
ini_set('display_errors', '0');
ini_set('log_errors', '1');
ini_set('error_log', $home . '/ootrando-php-errors.log');

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function done($status = 204) {
    http_response_code($status);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    done(405);
}

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$selfHost = preg_replace('/:\d+$/', '', strtolower($_SERVER['HTTP_HOST'] ?? ''));
if ($origin !== '' && strtolower(parse_url($origin, PHP_URL_HOST) ?? '') !== $selfHost) {
    done(403);
}

$raw = file_get_contents('php://input', false, null, 0, 65536);
$data = json_decode($raw ?: '', true);
if (!is_array($data) || !isset($data['message'])) {
    done(400);
}

$ip = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$visitor = substr(hash('sha256', $ip . '|ootrando'), 0, 10);
$counter = sys_get_temp_dir() . '/ootrando_log_' . $visitor;
$window = 600;
$limit = 30;
$count = 0;
if (is_file($counter) && time() - filemtime($counter) < $window) {
    $count = (int) @file_get_contents($counter);
}
if ($count >= $limit) {
    done(429);
}
@file_put_contents($counter, (string) ($count + 1));

$text = function ($key, $max) use ($data) {
    $value = $data[$key] ?? '';
    $value = is_scalar($value) ? (string) $value : json_encode($value);
    $value = preg_replace('/[^\P{C}\n\t]/u', '', $value) ?? '';
    return mb_substr($value, 0, $max);
};
$line = function ($value) {
    return trim(preg_replace('/\s+/', ' ', $value));
};

$fields = [
    'Where' => $line($text('where', 40)),
    'Error' => $line($text('message', 1000)),
    'Step' => $line($text('step', 200)),
    'Seed' => $line($text('seed', 40)),
    'Game' => $line($text('game', 100)),
    'File' => $line($text('file', 100)),
    'Source' => $line($text('source', 300)),
    'Status' => $line($text('status', 10)),
    'Build' => $line($text('build', 20)),
    'Device' => $line('memory ' . $text('memory', 10) . ' GB, ' . $text('cores', 10) . ' cores, screen ' . $text('screen', 20)),
    'Browser' => $line(mb_substr($_SERVER['HTTP_USER_AGENT'] ?? '', 0, 300)),
    'Visitor' => $visitor,
    'Settings' => $line($text('settings', 4000)),
    'Input' => $line($text('input', 2000)),
];
$entry = '==================== ' . gmdate('Y-m-d H:i:s') . " UTC ====================\n";
foreach ($fields as $label => $value) {
    if ($value !== '') {
        $entry .= str_pad($label . ':', 10) . $value . "\n";
    }
}
$detail = trim($text('detail', 12000));
if ($detail !== '') {
    $entry .= "Details:\n  " . str_replace("\n", "\n  ", $detail) . "\n";
}
$entry .= "\n";

$maxSize = 5 * 1024 * 1024;
foreach ([$home . '/ootrando-errors.log', __DIR__ . '/ootrando-errors.log'] as $file) {
    if (is_file($file) && filesize($file) > $maxSize) {
        @rename($file, $file . '.old');
    }
    if (@file_put_contents($file, $entry, FILE_APPEND | LOCK_EX) !== false) {
        @chmod($file, 0600);
        break;
    }
}
done();
