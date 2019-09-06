<?php
class General {
    public static function build_general($config) {
        $mainsettings = $config["main"];
        $ftpsettings = $config["ftp"];
        $httpsettings = $config["http"];

        $ftpsettings["pass"] = "******";
        $httpsettings["pwhash"] = "******";

        $html = "";

        $html .= "
<form action='/?site=generalsettings' method='post'>
<div class='generalsettings'>
    <h2>Daemon-Einstellungen</h2>
    <div class='singlesetting'>
        XML-Pfad:<br>
        <input type='text' class='littlewider' name='xmlpath' value='${mainsettings['xmlpath']}'>
    </div>
    <div class='singlesetting'>
        XML-Format:<br>
        <select name='xmlformat'>
            <option name='rmcu'>RMCU</option>
        </select>
        </div>
    <div class='singlesetting'>
        Speicherintervall [min]:<br>
        <input type='number' class='notsowide' name='save_interval' min='1' value='${mainsettings['save_interval']}'>
    </div>
    <div class='singlesetting'>
        Loggername (ID):<br>
        <input type='text' name='id' value='${mainsettings['id']}'>
    </div>
    <div class='singlesetting'>
        Loggernummer (SN):<br>
        <input type='text' name='sn' value='${mainsettings['sn']}'>
    </div>
    <div class='singlesetting'>
        IP-Adresse:<br>
        <input type='text' name='ip' value='${mainsettings['ip']}'>
    </div>
    <h2 class='margintop'>Weboberfläche</h2>
    <div class='singlesetting'>
        Benutzername:<br>
        <input type='text' name='http_user' value='${httpsettings['user']}'>
    </div>
    <div class='singlesetting'>
        Passwort:<br>
        <input type='password' name='http_pass' value='${httpsettings['pwhash']}'>
    </div>
    <h2 class='margintop'>FTP-Einstellungen (Optional)</h2>
    <div class='singlesetting'>
        Server:<br>
        <input type='text' class='littlewider' name='ftpserver' value='${ftpsettings['server']}'>
    </div>
    <div class='singlesetting'>
        Arbeitsverzeichnis:<br>
        <input type='text' class='littlewider' name='wdir' value='${ftpsettings['wdir']}'>
    </div>
    <div class='singlesetting'>
        Namensformat (strftime)<br>
        Beispiel: %Y-%m-%d_%H-%M-%S.xml<br>
        <input type='text' class='littlewider' name='fname' value='${ftpsettings['fname']}'>
    </div>
    <div class='singlesetting'>
        Benutzername:<br>
        <input type='text' name='ftp_user' value='${ftpsettings['user']}'>
    </div>
    <div class='singlesetting'>
        Passwort:<br>
        <input type='password' name='ftp_pass' value='${ftpsettings['pass']}'>
    </div>
    <div class='submit-container'>
        <input id='submit-save' type='submit' value='Speichern' name='submit-save'>
    </div>
</div>
</form>
        ";

        return $html;
    }
}