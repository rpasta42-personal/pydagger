var stdio = require('./stdio.js');
var TCPIOLib = stdio.TCPIOLib;

var client = new TCPIOLib('127.0.0.1', 7890, {});
var rpc = new stdio.jsonrpc(client, 'test')

rpc.on('connected', function() {
	rpc.call('hello', ['my', 'name', 'is', 'client'])
		.result(function(result) {
			console.log("Result: ", result);
		})
		.error(function(error){
			console.log("Error result: ", error);
		});

	rpc.call('error_method')
		.result(function(result) {
		})
		.error(function(error) {
			console.log("Error result: ", error);
		});
});

rpc.on('emit', function(evt) {
	console.log("EVENT", evt)
});

rpc.on('error', function(error) {
	console.log("RPC ERROR: ", error);
});

client.start()



/*
client.on('open', function() {
	console.log("Connected to server...")
	client.send("Hi Server!");
});

client.on('data', function(data) {
	console.log("[SERVER]", data)
});

client.on('close', function() {
	console.log("Connection closed...");
});

client.on('error', function(error) {
	console.log("Socket error: ", error);
});

client.start()
*/
