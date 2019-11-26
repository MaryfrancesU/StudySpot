function thinghappened(date) {
    $("#output").text($('dateCalender').html()); 
    console.log("sat hello");
};

function resetOptions(newOptions) {
    var currOptions = $("#formspotcontainer");
    $("#formspotcontainer").empty();

    for(let opt of newOptions) {
	$('<input type="radio" name=opt.name />').appendTo("#formspotcontainer");
    }
}

function changepref() {
    $.ajax({
	  "url": "localhost:5000/selection", //change from booking to selection
        "data": {
	      "date": $('dateCalender').html(),
		"food" : $('foodfilter').is(':checked'),
        // "time":
        // "pref" : {
	    //   "dummy": "sampletest",
        // },
        },
	  "type": "POST",
	  "dataType": "json"
	}).done(function (response){


	});

};

$('form').on('submit', function(event) {
$.ajax({
    'data' : {
        'date' : $('#dateCalender').val(),
    },
    'type' : 'POST',
    'url' : 'http://127.0.0.1:5000/book',
    'dataType' : 'json'
})
.done(function(data) {
    $('#output').text(data.output).show();
})
.fail(function(xhr, status, description){
    console.log("Error: " + description);
})
.always(function(xhr, status) {
    console.log("request complete w/ status: "+status);
});
event.preventDefault();
});
