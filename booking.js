function thinghappened(date) {
    $("#output").text($('dateCalender').html()); 
    console.log("sat hello");
};

function changepref() {
    $.ajax({
	  "url": "localhost:5000/selection", //change from booking to selection
        "data": {
	      "date": $('#dateCalender').html(),
		"stime": $('#starttime').html(),
		"etime": $('#endtime').html(),
		"food" : $('#foodfilter').prop('checked'),
		"quiet": $('#quietfilter').prop('checked'),
		"whisper": $('#whisperfilter').prop('checked'),
		"comp": $('#compfilter').prop('checked'),
	
        },
	  "type": "POST",
	  "dataType": "json"
	}).done(function (response){
	    var currOptions = $("#formspotcontainer");
   	    $("#formspotcontainer").empty();
	    
	    for(let opt of response) {
	    	var newSpot = $('<input type="radio" name="spot" />');
    	    	newSpot.appendTo(currOptions);
	    }
	    console.log("Successfully rechose"); 
	    
	}).fail(function(xhr, status, description){
    		console.log("Error: " + description);
	});

};
