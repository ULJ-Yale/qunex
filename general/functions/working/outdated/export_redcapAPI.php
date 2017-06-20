<?php

$data = array( 
	'token' => $argv[1],	
	'content' => $argv[2],
	'format' => $argv[3],
	'type' => $argv[4],
	'rawOrLabel' => $argv[5],
	'rawOrLabelHeaders' => $argv[6],

);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'https://poa-redcap.med.yale.edu/api/');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_VERBOSE, 0);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_AUTOREFERER, true);
curl_setopt($ch, CURLOPT_MAXREDIRS, 10);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
curl_setopt($ch, CURLOPT_FRESH_CONNECT, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data, '', '&'));
$output = curl_exec($ch);
print $output;
curl_close($ch);
