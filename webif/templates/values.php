<?php
class Values {
    public static function build_values($devices, $selected, $val_res) {
        $html = "";

        $device_selected = array();

        if (! $selected) {
            $device_selected[""] = "selected";
        } else {
            $device_selected[$selected] = "selected";
        }

        $html .= "
<form name='val-form' action='/' method='get'>
<input type='hidden' name='site' value='values'>
<div class='val-container'>
<h2>Werte anzeigen</h2>
<div class='singlesetting'>
Gerät auswählen:<br>
<select name='device' onchange='this.form.submit()'>
        <option value='' ${device_selected['']} disabled hidden></option>
";

        foreach ($devices as $dev) {
            $html .= "<option value='$dev' ${device_selected[$dev]}>$dev</option>";
        }

        $html .= "</select>";

        if ($val_res) {
            $html .= "<input type='submit' value='Aktualisieren' style='margin-left: 15px'>";
        }

        $html .= "</div>";

        if ($val_res) {
            $html .= "
<div class='values'>
<table>
<tr>
    <th style='width: 14em'>Zeit (UTC)</th>
    <th style='width: 6em'>MPID</th>
    <th>Wert</th>
</tr>
";
            foreach ($val_res as $val_data) {
                $html .= "
<tr>
    <td>${val_data[0]}</td>
    <td>${val_data[1]}</td>
    <td>${val_data[2]}</td>
</tr>";
            }
            $html .= "
</table>
</div>";
        }

        $html .= "
</div>
</form>
";
        return $html;
    }
}