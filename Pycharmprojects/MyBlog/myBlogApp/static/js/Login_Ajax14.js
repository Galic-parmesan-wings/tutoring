$(function () {
	$('form').on('submit', function(event) {
    event.preventDefault();
		$.ajax({
			data : {
				name : $('#validationCustomUsername').val(),
				email : $('#validationCustomPassword').val()
			},
			type : 'POST',
			url : '/login'
		})
		.done(function(data) {
			if(data.name){
				setTimeout(function () {
				 window.location.href = '/home'
				}, 1000);
			}
		});
	});
});