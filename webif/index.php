<?php
require "templates/device.php";
require "templates/general.php";
require "templates/log.php";
require "templates/values.php";
require "templates/upload.php";

session_start();

$CONFD_BASEPATH = "/etc/meterd/conf.d";

$baseconf = yaml_parse_file("/etc/meterd/main.yaml");

if (! $_SESSION["auth"]) {
    if(!isset($_SERVER["PHP_AUTH_USER"])) {
        header('WWW-Authenticate: Basic realm="meterd"');
    }

    $submitted_user = $_SERVER["PHP_AUTH_USER"];
    $submitted_pass = $_SERVER["PHP_AUTH_PW"];

    if ($submitted_user != "" &&
        (
          ($submitted_user == $baseconf["http"]["user"] &&
           $submitted_pass == password_verify($submitted_pass, $baseconf["http"]["pwhash"]))
          ||
          ($baseconf["http"]["user"] == "" && $submitted_user == "meterd" && $submitted_pass == "meterd")
        )
    ) {
        $_SESSION["auth"] = true;
    } else {
        header('HTTP/1.0 401 Unauthorized');
        print("401 Unauthorized");
        session_destroy();
        exit;
    }
}

$conflist = array();

$restart = $_GET["restart"];

$error = "";

$currentsite = $_GET["site"];
$currentdev = $_GET["device"];
$loggername = $baseconf["main"]["id"];

$currentdev_filename = "";

$loglist = array();

$devvals = array();

foreach (scandir($CONFD_BASEPATH) as $cfile) {
    if ($cfile == "." or $cfile == "..") continue;

    $parsed_config = yaml_parse_file("$CONFD_BASEPATH/$cfile");
    $tpid = $parsed_config["basic"]["tpid"];

    if (array_key_exists($tpid, $conflist)) {
        $error = "Die TPID $tpid existiert mehrfach!";
    }

    $conflist[$tpid] = $parsed_config;

    if ($tpid == $currentdev) {
        $currentdev_filename = $cfile;
    }
}

if($_POST) {
    if($currentsite == "conf") {
        # Build the config from the post parameters!
        $config = array();

        $config["basic"]["tpid"] = $_POST["tpid"];
        $config["basic"]["protocol"] = $_POST["protocol"];
        $config["basic"]["unit"] = (int) $_POST["unit"];
        $config["basic"]["query_interval"] = (int) $_POST["qinterval"];

        if ($_POST["protocol"] == "modbus_tcp") {
            $config["basic"]["address"] = $_POST["address"];
            $config["basic"]["register_offset"] = (int) $_POST["regoffset"];
        } elseif ($_POST["protocol"] == "modbus_rtu") {
            $config["basic"]["register_offset"] = (int) $_POST["regoffset"];
            $config["basic"]["device"] = $_POST["device"];
            $config["basic"]["baudrate"] = (int) $_POST["baudrate"];
            $config["basic"]["parity"] = $_POST["parity"];
        } elseif ($_POST["protocol"] == "mbus") {
            $config["basic"]["device"] = $_POST["device"];
            $config["basic"]["baudrate"] = (int) $_POST["baudrate"];
            $config["basic"]["parity"] = $_POST["parity"];
            $config["basic"]["converter_echo"] = $_POST["echo"] ? true : false;
        }

        if ($_POST["protocol"] == "mbus") {
            $datarecords = array();

            $rec_i = 0;
            while (true) {
                $existing = $_POST["$rec_i-datarecord"];
                $record_id = $_POST["record-$rec_i-record_id"];
                $mpid = $_POST["record-$rec_i-mpid"];
                $remark = $_POST["record-$rec_i-remark"];
                $factor = (double) $_POST["record-$rec_i-factor"];
                $offset = (int) $_POST["record-$rec_i-offset"];
                $round = $_POST["record-$rec_i-round"];

                if (! $existing) break;

                if ($_POST["submit-del"] === "$rec_i") {
                    $rec_i++;
                    continue;
                }

                $datarecords[] = array (
                    "record_id" => $record_id,
                    "mpid" => $mpid,
                    "remark" => $remark,
                    "factor" => $factor,
                    "offset" => $offset,
                    "round" => $round
                );

                $rec_i++;
            }

            if ($_POST["submit-add"]) {
                $datarecords[] = array (
                    "record_id" => "",
                    "mpid" => "",
                    "remark" => "",
                    "factor" => "",
                    "offset" => "",
                    "round" => ""
                );
            }

            $config["records"] = $datarecords;
        } else {
            $registers = array();

            $reg_i = 0;
            while (true) {
                $existing = $_POST["$reg_i-register"];
                $rstart = (int) $_POST["register-$reg_i-rstart"];
                $rcount = (int) $_POST["register-$reg_i-rcount"];
                $rtype = $_POST["register-$reg_i-type"];
                $endian = $_POST["register-$reg_i-endian"];
                $mpid = $_POST["register-$reg_i-mpid"];
                $remark = $_POST["register-$reg_i-remark"];
                $factor = (double) $_POST["register-$reg_i-factor"];
                $offset = (int) $_POST["register-$reg_i-offset"];
                $round = $_POST["register-$reg_i-round"];

                if (! $existing) break;

                if ($_POST["submit-del"] === "$reg_i") {
                    $reg_i++;
                    continue;
                }

                $registers[] = array(
                    "rstart" => $rstart,
                    "rcount" => $rcount,
                    "rtype" => $rtype,
                    "endian" => $endian,
                    "mpid" => $mpid,
                    "remark" => $remark,
                    "factor" => $factor,
                    "offset" => $offset,
                    "round" => $round
                );

                $reg_i++;
            }

            if ($_POST["submit-add"]) {
                $registers[] = array(
                    "rstart" => "",
                    "rcount" => "",
                    "rtype" => "",
                    "endian" => "",
                    "mpid" => "",
                    "remark" => "",
                    "factor" => "",
                    "offset" => "",
                    "round" => ""
                );
            }

            $config["registers"] = $registers;
        }

        $conflist[$currentdev] = $config;

        if ($_POST["submit-save"] && ! empty(trim($_POST["tpid"]))) {
            if (! (array_key_exists($_POST["tpid"], $conflist) && $_POST["tpid"] != $currentdev)) {
                if ($currentdev != $_POST["tpid"]) {
                    unset($conflist[$currentdev]);
                    $conflist[$_POST["tpid"]] = $config;
                }

                if ($currentdev_filename == "") $currentdev_filename = "${_POST['tpid']}.yaml";

                yaml_emit_file("$CONFD_BASEPATH/$currentdev_filename", $config);
            } else {
                $error = "Die TPID ${_POST['tpid']} existiert bereits!";
            }
        } elseif ($_POST["submit-delete"]) {
            unset($conflist[$currentdev]);
            unlink("$CONFD_BASEPATH/$currentdev_filename");
            $error = "Gerät wurde gelöscht.";
        } elseif ($_POST["copy-tpid-hidden"]) {
            if (! array_key_exists($_POST["copy-tpid-hidden"], $conflist)) {
                $config["basic"]["tpid"] = $_POST["copy-tpid-hidden"];
                yaml_emit_file("$CONFD_BASEPATH/${_POST['copy-tpid-hidden']}.yaml", $config);
                $conflist[$_POST["copy-tpid-hidden"]] = $config;
            } else {
                $error = "Die TPID ${_POST['copy-tpid-hidden']} existiert bereits!";
            }
        } elseif ($_POST["submit-download"]) {
            if (!empty($currentdev_filename)) {
                header('Content-Description: File Transfer');
                header('Content-Type: application/octet-stream');
                header('Content-Disposition: attachment; filename="'.$currentdev_filename.'"');
                header('Expires: 0');
                header('Cache-Control: must-revalidate');
                header('Pragma: public');
                header('Content-Length: '.filesize("$CONFD_BASEPATH/$currentdev_filename"));
                flush();
                readfile("$CONFD_BASEPATH/$currentdev_filename");
                exit;
            }
        }
    } elseif ($currentsite == "generalsettings") {
        if($_POST["http_user"]) {
            $baseconf["main"]["xmlpath"] = $_POST["xmlpath"];
            $baseconf["main"]["save_interval"] = (int)$_POST["save_interval"];
            $baseconf["main"]["id"] = $_POST["id"];
            $baseconf["main"]["sn"] = $_POST["sn"];
            $baseconf["main"]["ip"] = $_POST["ip"];

            $baseconf["ftp"]["server"] = $_POST["ftpserver"];
            $baseconf["ftp"]["wdir"] = $_POST["wdir"];
            $baseconf["ftp"]["fname"] = $_POST["fname"];
            $baseconf["ftp"]["user"] = $_POST["ftp_user"];

            if ($_POST["ftp_pass"] != "******") {
                $baseconf["ftp"]["pass"] = $_POST["ftp_pass"];
            }

            $baseconf["http"]["user"] = $_POST["http_user"];

            if ($_POST["http_pass"] != "******") {
                $baseconf["http"]["pwhash"] = password_hash($_POST["http_pass"], PASSWORD_DEFAULT);
            }

            if ($_POST["submit-save"]) {
                yaml_emit_file("/etc/meterd/main.yaml", $baseconf);
            }
        } else {
            $error = "Bitte einen Web-Benutzernamen festlegen.";
        }
    } elseif ($currentsite == "upload") {
        $uploaded_conf = yaml_parse_file($_FILES["file"]["tmp_name"]);

        if ($_POST["tpid"]) {
            $uploaded_conf["basic"]["tpid"] = $_POST["tpid"];
        }

        $tpid = $uploaded_conf["basic"]["tpid"];

        if (empty(trim($tpid))) {
            $error = "Die TPID kann nicht leer sein!";
        } elseif (array_key_exists($tpid, $conflist)) {
            $error = "Die TPID $tpid existiert bereits!";
        } else {
            yaml_emit_file("$CONFD_BASEPATH/$tpid.yaml", $uploaded_conf);
            $conflist[$tpid] = $uploaded_conf;
        }
    }
}

ksort($conflist);

$fp = stream_socket_client("unix://\0meterd", $errno, $errstr, 1);
if ($restart == "true") {
    fwrite($fp, "restart\n");
    $alive = "TRUE";
} else {
    fwrite($fp, "alive\n");
    $alive = fgets($fp);
}
fclose($fp);

if ($currentsite == "log") {
    $logfp = stream_socket_client("unix://\0meterd", $errno, $errstr, 1);
    fwrite($logfp, "log\n");

    while ($entry = fgets($logfp)) {
        $loglist[] = $entry;
    }
    fclose($logfp);
} elseif ($currentsite == "values" && $currentdev) {
    $valuesfp = stream_socket_client("unix://\0meterd", $errno, $errstr, 1);

    fwrite($valuesfp, "values $currentdev\n");

    while ($val = fgets($valuesfp)) {
        $devvals[] = explode("|", $val);
    }

    fclose($valuesfp);
}
?>

<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <?php
            print("<title>Meterd - $loggername</title>");
        ?>
        <meta name="author" content="">
        <meta name="description" content="">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <?php
            if ($restart && ($restart != "wait" || $alive != "TRUE")) {
                print("<meta http-equiv='refresh' content='1;url=/?restart=wait'/>");
            } elseif ($currentsite == "log") {
                print("<meta http-equiv='refresh' content='3;url=/?site=log'/>");
            }
        ?>

        <script language="javascript" type="text/javascript" src="main.js"></script>
        <link href="css/style.css" rel="stylesheet">
    </head>
    <body onload="disableenter()">
        <div class="wrapper">
            <div class="header">
                <div class="logo"><img id="konzern_logo" src="img/konzern_logo.png"></div>
                <div class="title"><h1>Meterd-Konfiguration</h1></div>
                <div class="isalive">
                    <?php
                        if($alive == "TRUE") {
                            print("<p class='green'>Daemon läuft</p>");
                            print("<a href='/?restart=true'>Neustarten</a>");
                        } else {
                            print("<p class='red'>Daemon gestoppt</p>");
                        }
                    ?>
                </div>
            </div>
            <div class="content">
                <div class="left">
                    <div class="mainsettings">
                        <h2>Allgemein</h2>
                        <ul>
                            <li><a href='/?site=generalsettings'>Einstellungen</a></li>
                            <li><a href='/?site=values'>Werte</a></li>
                            <li><a href='/?site=log'>Log</a></li>
                        </ul>
                    </div>
                    <div class="devices">
                        <h2>Geräte</h2>
                        <ul>
                            <?php
                                foreach($conflist as $tpid => $c) {
                                    if ($tpid == "") continue;

                                    print("<li><a href='/?site=conf&device=$tpid'>$tpid</a></li>");
                                }
                            ?>
                        </ul>
                        <a href='/?site=conf&device='>Neu</a><br>
                        <a href='/?site=upload'>Hochladen</a>
                    </div>
                </div>
                <div class="right">
                    <?php
                        if ($error) {
                            print("<p class='error'>$error</p>");
                        } elseif($restart) {
                            if ($restart == "wait" && $alive == "TRUE") {
                                print("Erfolgreich!");
                            } else {
                                print("Bitte warten...");
                            }
                        } elseif($currentsite == "conf") {
                            print(Device::build_device($currentdev_filename, $conflist[$currentdev]));
                        } elseif ($currentsite == "generalsettings") {
                            print(General::build_general($baseconf));
                        } elseif ($currentsite == "log") {
                            print(Log::build_log($loglist));
                        } elseif ($currentsite == "values") {
                            print(Values::build_values(array_keys($conflist), $currentdev, $devvals));
                        } elseif ($currentsite == "upload") {
                            print(Upload::build_upload());
                        } elseif ($currentsite == "") {
                            print("
                            Meterd (c) 2019 Florian Bührle<br><br>
                            pyMeterBus (c) 2014 Mikael Ganehag Brorsson<br>
                            /usr/local/meterd/lib/meterbus/LICENSE<br><br>
                            PyYAML (c) 2017-2019 Ingy döt Net, (c) 2006-2016 Kirill Simonov<br>
                            /usr/local/meterd/lib/yaml/LICENSE
                            ");
                        }
                    ?>
                </div>
            </div>
        </div>
    </body>
</html>