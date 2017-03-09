<?php
$data = array(
    'token' => '570BB42B2217DBA7BB6F2146B4FE15D3',
    'content' => 'record',
    'format' => 'csv',
    'type' => 'flat',
    'forms' => array('blackthorn_fmri'),
    'events' => array('4_blackthorn_arm_1'),
    'rawOrLabel' => 'raw',
    'rawOrLabelHeaders' => 'label',
    'exportCheckboxLabel' => 'false',
    'returnFormat' => 'csv'
);

var_dump($data);

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

