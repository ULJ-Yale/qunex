<?php


$data = array( 
     'token' => $argv[1],
     'content' => $argv[2],
     'format' => $argv[3],
     //'type' => array(str_replace("|","\",\"",$argv[4])),
     'type' => array(str_replace("|","\",\"",$argv[4])),
     'records' => $argv[5],
     //'fields' => array(str_replace("|","\",\"",$argv[6])),
     //'forms' => array(str_replace("|","\",\"",$argv[7])), 
     //'events' => array(str_replace("|","\",\"",$argv[8])),
     'rawOrLabel' => $argv[9],
     'rawOrLabelHeaders' => $argv[10],
     'exportCheckboxLabel' => $argv[11],
     'returnFormat' => $argv[12] ,
     'exportSurveyFields' => $argv[13],
     'exportDataAccessGroups' => $argv[14],
     'filterLogic' => $argv[15],
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



