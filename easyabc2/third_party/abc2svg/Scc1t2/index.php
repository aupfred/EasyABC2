<!DOCTYPE html>
<html>
<meta charset="utf-8" />
<title>Jef Moine - abc2svg files</title>
<style>td{padding:0 0.5em}</style>

<body bgcolor="#faf0e6">
<h2>abc2svg</h2>

<h3>abc2svg sound font</h3>

<table border="1" style="border-collapse: collapse">
<tr>	<th><a href="?sort=name">Name</a></th>
	<th>Size</th>
	<th><a href="?sort=date">Date</a></th></tr>
<?php
function fmt_sz($fn)
{
	$bytes = filesize($fn);
	if ($bytes < 1024) return $bytes;
	elseif ($bytes < 1048576) return round($bytes / 1024, 2).'K';
	else return round($bytes / 1048576, 2).'M';
}
$cdir = glob('*');
if ($_GET['sort'] == 'date') {
	usort($cdir, function($a, $b) {
		return filemtime($b) - filemtime($a);
	});
}
foreach ($cdir as $fn) {
    if (!in_array($fn, array(".", "..", "index.php"))) {
	$dt = date("Y-m-d H:i", filemtime($fn));
	$sz = fmt_sz($fn);
	echo "<tr><td><a href=\"$fn\">$fn</a></td>";
	echo "<td style=\"text-align:right\">$sz</td><td>$dt</td></tr>\n";
    }
}
?>
</table>
</html>
