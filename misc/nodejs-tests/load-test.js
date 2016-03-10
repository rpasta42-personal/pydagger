var test_mod = require('test');

var test = new test_mod('/tmp/test.sock');

test.on('connected', function() {
	console.log('connected');

	test.hello("John", "Doe")
		.result(function(result) {
			console.log('result', result)
		})
		.error(function(error) {
			console.log('error', error);
		});
});

test.on('error', function(error) {
	console.log("Unhandled Error", error);
});

test.on('test_event', function() {
	console.log("GOT TEST EVENT", arguments);
});

test.start();
