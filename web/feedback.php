<?php
ini_set('display_errors', '0');
ini_set('log_errors', '1');
ini_set('error_log', dirname($_SERVER['DOCUMENT_ROOT'] ?? __DIR__) . '/ootrando-php-errors.log');
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function reply($ok, $error = null, $status = 200) {
    http_response_code($status);
    echo json_encode($ok ? ['ok' => true] : ['ok' => false, 'error' => $error]);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    reply(false, 'Method not allowed.', 405);
}

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$selfHost = strtolower($_SERVER['HTTP_HOST'] ?? '');
if ($origin !== '' && strtolower(parse_url($origin, PHP_URL_HOST) ?? '') !== preg_replace('/:\d+$/', '', $selfHost)) {
    reply(false, 'Forbidden.', 403);
}

$to = 'IcePeten@gmail.com';
$kinds = ['Feedback', 'Feature Request', 'Bug Report', 'Logic Problem'];

$clean = function ($value, $max) {
    $value = is_string($value) ? $value : '';
    return trim(mb_substr($value, 0, $max));
};
$oneLine = function ($value) {
    return preg_replace('/[\r\n\t]+/', ' ', $value);
};

if ($clean($_POST['website'] ?? '', 200) !== '') {
    reply(true);
}

$kind = in_array($_POST['kind'] ?? '', $kinds, true) ? $_POST['kind'] : 'Feedback';
$name = $oneLine($clean($_POST['name'] ?? '', 100));
$email = $oneLine($clean($_POST['email'] ?? '', 200));
$message = $clean($_POST['message'] ?? '', 5000);
$settings = $clean($_POST['settings'] ?? '', 4000);
$seed = $oneLine($clean($_POST['seed'] ?? '', 40));

if (mb_strlen($message) < 5) {
    reply(false, 'Please write a little more before sending.', 400);
}
if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    reply(false, 'That email address does not look right.', 400);
}

$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$stamp = sys_get_temp_dir() . '/ootrando_feedback_' . hash('sha256', $ip);
if (is_file($stamp) && time() - filemtime($stamp) < 60) {
    reply(false, 'Thanks! Please wait a minute before sending another message.', 429);
}
@touch($stamp);

$host = strtolower(preg_replace('/^www\./i', '', $_SERVER['HTTP_HOST'] ?? 'ootrando.com'));
$host = preg_replace('/[^a-z0-9.-]/', '', $host) ?: 'ootrando.com';
$from = "noreply@$host";

$subject = "[OoT Randomizer] $kind" . ($name !== '' ? " from $name" : '');
$lines = [
    "Type: $kind",
    'Name: ' . ($name !== '' ? $name : '(not given)'),
    'Email: ' . ($email !== '' ? $email : '(not given)'),
];
if ($seed !== '') {
    $lines[] = "Seed: $seed";
}
$lines[] = '';
$lines[] = $message;
if ($settings !== '') {
    $lines[] = '';
    $lines[] = 'Settings string:';
    $lines[] = $settings;
}
$lines[] = '';
$lines[] = '---';
$lines[] = 'Sent from ' . $host . ' on ' . gmdate('Y-m-d H:i') . ' UTC';
$lines[] = 'Browser: ' . $oneLine($clean($_SERVER['HTTP_USER_AGENT'] ?? '', 300));

$headers = [
    'From: OoT Randomizer <' . $from . '>',
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
];
if ($email !== '') {
    $headers[] = 'Reply-To: ' . ($name !== '' ? '"' . str_replace('"', '', $name) . '" ' : '') . "<$email>";
}

$encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
$body = implode("\r\n", $lines);

$entry = "==================== " . gmdate('Y-m-d H:i:s') . " UTC ====================\n"
    . "Subject: $subject\n" . str_replace("\r\n", "\n", $body) . "\n\n";
$saved = false;
foreach ([dirname($_SERVER['DOCUMENT_ROOT'] ?? __DIR__) . '/ootrando-feedback.txt', __DIR__ . '/feedback-inbox.log'] as $inbox) {
    if (@file_put_contents($inbox, $entry, FILE_APPEND | LOCK_EX) !== false) {
        @chmod($inbox, 0600);
        $saved = true;
        break;
    }
}

$relay = [
    '_subject' => $subject,
    '_template' => 'box',
    '_captcha' => 'false',
    'Type' => $kind,
    'Name' => $name !== '' ? $name : '(not given)',
    'Email' => $email !== '' ? $email : '(not given)',
    'Seed' => $seed !== '' ? $seed : '(none)',
    'Message' => $message,
    'Settings' => $settings !== '' ? $settings : '(none)',
];
if ($email !== '') {
    $relay['_replyto'] = $email;
}
$relayHeaders = "Content-Type: application/json\r\nAccept: application/json\r\nReferer: https://ootrando.com/\r\nOrigin: https://ootrando.com\r\n";
$response = @file_get_contents('https://formsubmit.co/ajax/' . rawurlencode($to), false, stream_context_create([
    'http' => ['method' => 'POST', 'header' => $relayHeaders, 'content' => json_encode($relay), 'timeout' => 15, 'ignore_errors' => true],
]));
$result = is_string($response) ? json_decode($response, true) : null;
$sent = is_array($result) && in_array($result['success'] ?? null, [true, 'true'], true);

if (!$sent) {
    $sent = @mail($to, $encodedSubject, $body, implode("\r\n", $headers), '-f' . $from);
}
if (!$sent) {
    $sent = @mail($to, $encodedSubject, $body, implode("\r\n", $headers));
}
if (!$sent && !$saved) {
    reply(false, 'The message could not be sent right now.', 500);
}
reply(true);
