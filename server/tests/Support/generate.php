<?php

// One-time generator for the offline verifier test keys.
// Run from server/: with OPENSSL_CONF pointing at a working openssl.cnf:
//   $env:OPENSSL_CONF='<php>\extras\ssl\openssl.cnf'; php tests/Support/generate.php

if (! is_dir(__DIR__)) {
    mkdir(__DIR__, 0777, true);
}

$key = openssl_pkey_new([
    'private_key_bits' => 2048,
    'private_key_type' => OPENSSL_KEYTYPE_RSA,
]);

if ($key === false) {
    echo "KEYGEN FAILED\n";
    exit(1);
}

openssl_pkey_export($key, $privatePem);

$dn = ['commonName' => 'securetoken.test'];
$csr = openssl_csr_new($dn, $key, ['digest_alg' => 'sha256']);
$certificate = openssl_csr_sign($csr, null, $key, 3650, ['digest_alg' => 'sha256']);
openssl_x509_export($certificate, $certificatePem);

file_put_contents(__DIR__.'/private.pem', $privatePem);
file_put_contents(__DIR__.'/certificate.pem', $certificatePem);

// A second key that is never published: signs forged tokens in tests.
$impostor = openssl_pkey_new([
    'private_key_bits' => 2048,
    'private_key_type' => OPENSSL_KEYTYPE_RSA,
]);
openssl_pkey_export($impostor, $impostorPem);
file_put_contents(__DIR__.'/impostor.pem', $impostorPem);

echo "OK: wrote private.pem + certificate.pem + impostor.pem\n";
