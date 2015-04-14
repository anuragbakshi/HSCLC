var clock;
		
		$(document).ready(function() {

			var a = new Date();
			var b = new Date("November 1, 2014 11:59:59");
			var difference = (b - a) / 1000;
			
			clock = jQuery('#clockman').FlipClock( difference, {
		        clockFace: 'DailyCounter'
		    });

		   // clock.start(function() {});

		    //clock.setTime(3600);
		    clock.setCountdown(true);
		    clock.start(function() {});
		});