<?php
class Log {
    public static function build_log($loglist) {
        $html = "";

        $html .= "<div class='log-container'><h2>Log</h2>";
        foreach ($loglist as $entry) {
            $html .= "<p class='logentry'>$entry</p>";
        }
        $html .= "</div>";

        return $html;
    }
}