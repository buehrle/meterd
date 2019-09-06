<?php
class Device {
    public static function build_device($filename, $config) {
        $html = "";

        $baseconf = $config["basic"];

        $protocol_selected = array();
        $protocol_selected[$baseconf["protocol"]] = "selected";

        $parity_selected = array();
        if($baseconf["parity"] == ""){
            $baseconf["parity"] = "N";
        }
        $parity_selected[$baseconf["parity"]] = "selected";

        $converter_echo = "";

        if ($baseconf["converter_echo"]) {
            $converter_echo = "checked";
        }

        $singlesettings = array();

        $dataholder_visibility = array();

        $dataholder_visibility["registers"] = "hidden";
        $dataholder_visibility["datarecords"] = "hidden";

        $submit_disabled = "";
        $submit_filebased_disabled = "";

        $title = "Gerät ändern";

        if ($baseconf["protocol"] == "modbus_tcp") {
            $singlesettings["device"] = "hidden";
            $singlesettings["baudrate"] = "hidden";
            $singlesettings["parity"] = "hidden";
            $singlesettings["echo"] = "hidden";
            $dataholder_visibility["registers"] = "";
        } elseif ($baseconf["protocol"] == "modbus_rtu") {
            $singlesettings["address"] = "hidden";
            $singlesettings["echo"] = "hidden";
            $dataholder_visibility["registers"] = "";
        } elseif ($baseconf["protocol"] == "mbus") {
            $singlesettings["address"] = "hidden";
            $singlesettings["regoffset"] = "hidden";
            $dataholder_visibility["datarecords"] = "";
        } else {
            $protocol_selected["none"] = "selected";
            $submit_disabled = "disabled";
            $title = "Gerät hinzufügen";
        }

        if (! $filename || $submit_disabled) {
            $submit_filebased_disabled = "disabled";
        }

        if (! $config["registers"]) {
            $config["registers"][] = array();
        }

        if (! $config["records"]) {
            $config["records"][] = array();
        }

        $html .= "
<form name='device-form' action='/?site=conf&device=${baseconf['tpid']}' method='post'>
<h2>$title</h2>
<div class='dev-mainsettings'>
<div class='rightleft'>
<div class='singlesetting'>
    TPID:<br><input type='text' name='tpid' value='${baseconf['tpid']}'>
</div>
<div class='singlesetting'>
    Protokoll:<br>
    <select name='protocol' onchange='setvisibility(this.selectedIndex)'>
        <option value='' ${protocol_selected['none']} disabled hidden></option>
        <option value='modbus_tcp' ${protocol_selected['modbus_tcp']}>Modbus TCP</option>
        <option value='modbus_rtu' ${protocol_selected['modbus_rtu']}>Modbus RTU</option>
        <option value='mbus' ${protocol_selected['mbus']}>MBus</option>
    </select>
</div>
<div class='singlesetting'>
    Bus-ID:<br><input type='number' name='unit' min='0' max='255' value='${baseconf['unit']}'>
</div>
<div class='singlesetting'>
    Abfrageintervall [s]:<br><input type='number' name='qinterval' min='1' value='${baseconf['query_interval']}'>
</div>
</div>
<div class='rightright'>
<div class='singlesetting address ${singlesettings['address']}'>
    IP-Addresse:<br><input type='text' name='address' value='${baseconf['address']}'>
</div>
<div class='singlesetting regoffset ${singlesettings['regoffset']}'>
    Register-Versatz:<br><input type='number' name='regoffset' value='${baseconf['register_offset']}'>
</div>
<div class='singlesetting device ${singlesettings['device']}'>
    Serielles Gerät:<br><input type='text' name='device' value='${baseconf['device']}'>
</div>
<div class='singlesetting baudrate ${singlesettings['baudrate']}'>
    Baudrate:<br><input type='text' name='baudrate' value='${baseconf['baudrate']}'>
</div>
<div class='singlesetting parity ${singlesettings['parity']}'>
    Parität:<br>
     <select name='parity'>
        <option value='O' ${parity_selected['O']}>Odd</option>
        <option value='E' ${parity_selected['E']}>Even</option>
        <option value='N' ${parity_selected['N']}>Keine</option>
    </select>
</div>
<div class='singlesetting echo ${singlesettings['echo']}'>
    Pegelwandler-Echo:<br><input type='checkbox' name='echo' value='echo' $converter_echo>
</div>
</div>
</div>
<div class='registers ${dataholder_visibility['registers']}'>
    <h2>
        Register    
    </h2>
    <table>
        <tr>
            <th></th>
            <th>Start</th>
            <th>Anzahl</th>
            <th>Typ</th>
            <th>Endian</th>
            <th>MPID</th>
            <th class='fullwidth'>Bemerkung</th>
            <th>Faktor</th>
            <th>Versatz</th>
            <th>Rnd</th>
        </tr>";

            foreach ($config["registers"] as $reg_i => $register) {
                $rtype_selected = array();
                $endian_selected = array();

                $rtype_selected[$register['rtype']] = "selected";
                $endian_selected[$register['endian']] = "selected";

                $html .= "
                   <tr>
                       <input type='hidden' id='$reg_i-register' name='$reg_i-register' value='1'>
                       <td><input class='del' name='submit-del' type='submit' value='$reg_i'></td>
                       <td><input type='number' name='register-$reg_i-rstart' min='0' max='65535' value='${register['rstart']}'></td>
                       <td><input type='number' name='register-$reg_i-rcount' min='1' max='4' value='${register['rcount']}'></td>
                       <td>
                           <select name='register-$reg_i-type'>
                               <option value='int' ${rtype_selected['int']}>Int</option>
                               <option value='uint' ${rtype_selected['uint']}>UInt</option>
                               <option value='float' ${rtype_selected['float']}>Float</option>
                           </select>
                       </td>
                       <td>
                           <select name='register-$reg_i-endian'>
                               <option value='big' ${endian_selected['big']}>Big</option>
                               <option value='little' ${endian_selected['little']}>Little</option>
                           </select>
                       </td>
                       <td><input type='text' name='register-$reg_i-mpid' value='${register['mpid']}'></td>
                       <td class='remarkcontainer'><input class='fullwidth' type='text' name='register-$reg_i-remark' value='${register['remark']}'></td>
                       <td><input class='notsowide' type='text' name='register-$reg_i-factor' value='${register['factor']}'></td>
                       <td><input class='notsowide' type='number' name='register-$reg_i-offset' value='${register['offset']}'></td>
                       <td><input class='notsowide' type='number' name='register-$reg_i-round' value='${register['round']}'></td>
                   </tr> 
                ";
            }

            $html .= "
            <tr>
                <td><input class='add' name='submit-add' type='submit' value='add'></td>
            </tr>
    </table>
</div>
<div class='datarecords ${dataholder_visibility['datarecords']}'>
    <h2>Datarecords</h2>
    <table>
        <tr>
            <th></th>
            <th>Rec. ID</th>
            <th>MPID</th>
            <th class='fullwidth'>Bemerkung</th>
            <th>Faktor</th>
            <th>Versatz</th>
            <th>Rnd</th>
        </tr>";

            foreach ($config["records"] as $rec_i => $record) {
                $html .= "
                   <tr>
                       <input type='hidden' id='$rec_i-datarecord' name='$rec_i-datarecord' value='1'>
                       <td><input class='del' name='submit-del' type='submit' value='$rec_i'></td>
                       <td><input type='text' name='record-$rec_i-record_id' value='${record['record_id']}'></td>
                       <td><input type='text' name='record-$rec_i-mpid' value='${record['mpid']}'></td>
                       <td class='remarkcontainer'><input class='fullwidth' type='text' name='record-$rec_i-remark' value='${record['remark']}'></td>
                       <td><input class='notsowide' type='text' name='record-$rec_i-factor' value='${record['factor']}'></td>
                       <td><input class='notsowide' type='number' name='record-$rec_i-offset' value='${record['offset']}'></td>
                       <td><input class='notsowide' type='number' name='record-$rec_i-round' value='${record['round']}'></td>
                   </tr>
                ";
            }

            $html .= "
            <tr>
                <td><input class='add' name='submit-add' type='submit' value='add'></td>
            </tr>
    </table>
</div>
<div class='submit-container'>
    <input id='submit-save' type='submit' value='Speichern' name='submit-save' $submit_disabled>
    <input id='submit-copy' class='submit-leftmargin' type='button' value='Duplizieren' name='submit-copy' onclick='askforname()' $submit_filebased_disabled>
    <input id='submit-download' class='submit-leftmargin' type='submit' value='Herunterladen' name='submit-download' $submit_filebased_disabled>
    <input id='submit-delete' type='submit' value='Gerät löschen' name='submit-delete' $submit_filebased_disabled>
</div>
<input type='hidden' id='copy-tpid-hidden' name='copy-tpid-hidden' value=''>
</form>
";

        return $html;
    }
}