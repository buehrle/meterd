<?php
class Upload {
    public static function build_upload() {
        $html = "
<div>
<form enctype='multipart/form-data' name='upload-form' action='/?site=upload' method='post'>
<h2>Konfiguration hochladen</h2>
<div class='singlesetting'>
<input type='file' name='file' value='Datei auswählen'>
</div>
<div class='singlesetting margintop'>
TPID:<br>
<input type='text' name='tpid' placeholder='Aus Datei übernehmen'>
</div>
<div class='submit-container'>
<input type='submit' name='submit-upload' value='Hochladen'>
</div>
</form>
</div>";


        return $html;
    }
}