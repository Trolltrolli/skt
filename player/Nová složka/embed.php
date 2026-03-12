<?php
require_once(__DIR__ . '/includes/autoload.php');

$volume = $settings['volume'];

// Start displaying the Feed
$player = new player();
$player->db = $db;
$player->url = $CONF['url'];
$player->l_per_post = $settings['lperpost'];
$player->title = $settings['title'];

// Get the track
$player = $player->getEmbed($_GET['id']);

// Match the content from the song-title class in order to set it for the title tag
preg_match_all('/<div.*(class="song-title").*>([\d\D]*)<\/div>/iU', $player, $title);

// Get the token_id
$token_id = generateToken();
mysqli_close($db);
?>
<!DOCTYPE html>
<html class="<?php echo $LNG['lang_dir']; ?>" dir="<?php echo $LNG['lang_dir']; ?>">
<head>
<meta charset="UTF-8" />
<title><?php echo ((!empty($title[2][0])) ? strip_tags($title[2][0]).' - '.$settings['title'] : $settings['title']); ?></title>
<link href="<?php echo $CONF['url'].'/'.$CONF['theme_url']; ?>/style.css" rel="stylesheet" type="text/css">
<meta name="viewport" content="width=device-width, minimum-scale=1.0, maximum-scale=1.0">
<script type="text/javascript">baseUrl = '<?php echo $CONF['url']; ?>'; token_id = '<?php echo $token_id; ?>'; viewed_id = 0; player_volume = '<?php echo $volume; ?>';  lng_just_now = '<?php echo $LNG['just_now']; ?>'; lng_ta_second = '<?php echo $LNG['ta_second']; ?>'; lng_ta_seconds = '<?php echo $LNG['ta_seconds']; ?>'; lng_ta_minute = '<?php echo $LNG['ta_minute']; ?>'; lng_ta_minutes = '<?php echo $LNG['ta_minutes']; ?>'; lng_ta_hour = '<?php echo $LNG['ta_hour']; ?>'; lng_ta_hours = '<?php echo $LNG['ta_hours']; ?>'; lng_ta_day = '<?php echo $LNG['ta_day']; ?>'; lng_ta_days = '<?php echo $LNG['ta_days']; ?>'; lng_ta_week = '<?php echo $LNG['ta_week']; ?>'; lng_ta_weeks = '<?php echo $LNG['ta_weeks']; ?>'; lng_ta_month = '<?php echo $LNG['ta_month']; ?>'; lng_ta_months = '<?php echo $LNG['ta_months']; ?>'; lng_ta_year = '<?php echo $LNG['ta_year']; ?>'; lng_ta_years = '<?php echo $LNG['ta_years']; ?>'; lng_ago = '<?php echo $LNG['ago']; ?>'; lng_dir = '<?php echo $LNG['lang_dir']; ?>';</script>
<script type="text/javascript" src="<?php echo $CONF['url'].'/'.$CONF['theme_url']; ?>/js/jquery.js"></script>
<script type="text/javascript" src="<?php echo $CONF['url'].'/'.$CONF['theme_url']; ?>/js/functions.js"></script>
<script type="text/javascript" src="<?php echo $CONF['url'].'/'.$CONF['theme_url']; ?>/js/jquery.jplayer.min.js"></script>
<script type="text/javascript" src="<?php echo $CONF['url'].'/'.$CONF['theme_url']; ?>/js/jquery.timeago.js"></script>
<script type="text/javascript">
$(document).ready(function() {
<?php
if(isset($_GET['autoplay'])) {
?>
	setTimeout(function() {
		$("#play<?php echo $_GET['id']; ?>").trigger('click');
	},10);
<?php
}
?>
});
function playSong(song, id, format) {
	// Remove the current-song class
	$('.current-song').removeClass('current-song');
	// Show the previously hidden Play button (if any)
	$('.current-play').show();
	$('.current-play').removeClass('current-play');

	// Remove the active player if exist and set the ghost player
	$('.current-seek').html($('#sound_ghost_player').html());

	// Remove the active player class
	$('.current-seek').removeClass('current-seek');

	// Add the current song class
	$('#track'+id).addClass('current-song');
	// Add current play class to the Play button and hide it
	$('#play'+id).addClass('current-play');
	$('.current-play').hide();

	// Get the current played song name
	if ($('#song-name'+id).html().length > 25) {
		var songName = $('#song-name'+id).html().substr(0, 25)+'...';
	} else {
		var songName = $('#song-name'+id).html();
	}
	
	$('#sw-song-name').html(songName);

	// Show the time holder when a song starts playing
	$('.jp-audio .jp-time-holder').show();

	// Add the active player to the current song
	$("#song-controls"+id).html($("#seek-bar-song").html());

	// Add the active player class to the current song
	$("#song-controls"+id).addClass('current-seek');

    // Set the play/pause button position (this is needed for mobile view in order for the play/pause button to be at the same height with the initial play button)
    if(lng_dir == "rtl") {
        $('#track'+id+' .jp-play , #track'+id+' .jp-pause').css({ 'margin-top' : '-' + $('.song-top', '#track'+id).outerHeight() + 'px', 'right' : '0' });
    } else {
        $('#track'+id+' .jp-play , #track'+id+' .jp-pause').css({ 'margin-top' : '-' + $('.song-top', '#track'+id).outerHeight() + 'px' });
    }

	// if the format is mp4, switch it to m4a since mp4 can be audio only
	if(format == 'mp4') {
		format = 'm4a';
	}

	$("#sound-player").jPlayer({
		ready: function (event) {
			if(format == 'mp3') {
				$(this).jPlayer("setMedia", {
					mp3: song
				}).jPlayer("play");
			} else if(format == 'm4a') {
				$(this).jPlayer("setMedia", {
					m4a: song				
				}).jPlayer("play");
			}
		},
		play: function() {
			// Verify if a view has been added already for this track
			if(viewed_id == id) {
				return false;
			}
			// Add the play count
			viewed_id = id;
			$.ajax({
				type: "POST",
				url: "<?php echo $CONF['url']; ?>/requests/add_view.php",
				data: "id="+id+"&token_id=<?php echo $token_id; ?>", 
				cache: false,
				success: function(html) {
				
				}
			});
		},
		ended: function() {
			viewed_id = 0;
		},
		cssSelectorAncestor: '.sound-container',
		error: function() {
			// If the track fails to play for whatever reasons, hide it
			$('#track'+id).fadeOut();
		},
		swfPath: "<?php echo $CONF['url'].'/'.$CONF['theme_url']; ?>/js",
		supplied: format,
		wmode: "window",
		volume: player_volume,
		smoothPlayBar: true,
		keyEnabled: true
	});
};
</script>
</head>
<body>
<?php
echo $player;
?>
<div id="sound-player" class="jp-jplayer"></div>
<div id="seek-bar-song" style="display: none;">
	<div class="sound-container jp-audio">
		<div class="jp-type-single">
				<div class="jp-gui jp-interface">
					<a class="jp-play">&nbsp;</a><a class="jp-pause">&nbsp;</a>
					<div class="jp-progress">
						<div class="jp-seek-bar">
							<div class="jp-play-bar"></div>
						</div>
					</div>
					<div class="jp-time-holder">
						<div class="jp-current-time"></div>
						<div class="jp-duration"></div>
					</div>
			</div>
		</div>
	</div>
</div>
<div id="sound_ghost_player" style="display: none;"><div class="jp-audio"><div class="jp-type-single"><div class="jp-gui jp-interface"><div class="jp-progress"><div class="jp-seek-bar"><div class="jp-play-bar"></div></div></div></div></div></div></div><script>document.addEventListener("DOMContentLoaded", () => {    console.log("📻 Skript spuštěn – čekám na jPlayer...");    if (window.jQuery && jQuery().jPlayer) {        console.log("✅ jPlayer je načten");        const player = jQuery(".jp-jplayer");        if (player.length > 0) {            console.log("▶️ Hledám přehrávač... nalezen");            // MP3 přehrává            player.bind($.jPlayer.event.playing, function () {                console.log("✅ MP3 se přehrává – posílám OK");                window.parent.postMessage({ fm_status: "ok" }, "*");            });            // Chyba při přehrání            player.bind($.jPlayer.event.error, function (e) {                console.log("❌ Chyba jPlayeru:", e.jPlayer.error.type);                window.parent.postMessage({ fm_status: "fail" }, "*");            });            // Zjištění, že je MP3 skutečně načtena (loadedmetadata)            player.bind($.jPlayer.event.loadeddata, function (e) {                const dur = player.data("jPlayer").status.duration;                if (dur > 0) {                    console.log("🎵 MP3 načtena, délka:", dur, "sekund");					window.parent.postMessage({ mp3_status: "ok" }, "*");                } else {                    console.log("⚠️ MP3 nebyla správně načtena (duration = 0)");                    window.parent.postMessage({ fm_status: "fail" }, "*");                }            });            // Zkusíme automatické přehrání            console.log("🔈 Pokus o přehrání s hlasitostí 0");            player.jPlayer("volume", 0).jPlayer("play");        } else {            console.warn("⚠️ .jp-jplayer nenalezen – kontrola chybového textu");            const errCheck = setInterval(() => {                if (document.body.innerText.includes("Sorry, we couldn't find the requested track")) {                    clearInterval(errCheck);                    console.log("❌ Textová chyba detekována – posílám FAIL");                    window.parent.postMessage({ fm_status: "fail" }, "*");                }            }, 500);            setTimeout(() => {                clearInterval(errCheck);                console.log("🕒 Konec čekání na chybový text");            }, 5000);        }    } else {        console.warn("❗ jPlayer nenalezen – posílám FAIL");        window.parent.postMessage({ fm_status: "fail" }, "*");    }});</script>
</body>
</html>